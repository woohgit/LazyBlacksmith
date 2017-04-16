# -*- encoding: utf-8 -*-
from flask import Blueprint
from flask import jsonify
from flask import request
from flask_login import current_user
from flask_login import login_required
from sqlalchemy import func

from lazyblacksmith.models import IndustryIndex
from lazyblacksmith.models import SolarSystem
from lazyblacksmith.models import TokenScope
from lazyblacksmith.models import db
from lazyblacksmith.utils.json import json_response

from . import logger

ajax_account = Blueprint('ajax_account', __name__)


@ajax_account.route('/scopes/<int:character_id>/<scope>', methods=['DELETE'])
@login_required
def delete_scope(character_id, scope):
    """ Remove a scope for a given character_id from the database """
    if request.is_xhr:
        allowed_character_id = [
            alt.character_id for alt in current_user.alts_characters.all()
        ]
        if (character_id == current_user.character_id or
                character_id in allowed_character_id):
            try:
                TokenScope.query.filter(
                    TokenScope.user_id == character_id,
                    TokenScope.scope == scope
                ).delete()
                db.session.commit()
                return json_response('success', '', 200)

            except:
                logger.exception('Cannot delete scope %s for user_id %s' % (
                    scope,
                    character_id,
                ))
                db.session.rollback()
                return json_response('danger',
                                     'Error while trying to delete scope',
                                     500)
        else:
            return json_response('danger',
                                 'This character does not belong to you',
                                 500)
    else:
        return 'Cannot call this page directly', 403


@ajax_account.route('/user_preference/', methods=['POST'])
@login_required
def update_user_industry_preference():
    """ Update the user preferences for industry """
    if request.is_xhr:
        preferences = request.get_json()

        if 'production' in preferences:
            return update_production_preference(preferences['production'])

        if 'research' in preferences:
            return update_research_preference(preferences['research'])

        if 'invention' in preferences:
            return update_invention_preference(preferences['invention'])
    else:
        return 'Cannot call this page directly', 403


def update_production_preference(preferences):
    """ Called by update_user_industry_preference, update the production
    preferences """
    if preferences:
        pref = current_user.pref

        try:
            solar_system, check_main = check_solar_system_name_index(
                preferences['system']
            )
            solar_system_subcomp, check_sub = check_solar_system_name_index(
                preferences['componentSystem']
            )
            if check_main:
                pref.prod_system = solar_system
            if check_sub:
                pref.prod_sub_system = solar_system_subcomp

            pref.prod_facility = preferences['facility']
            pref.prod_me_rig = preferences['meRig']
            pref.prod_te_rig = preferences['teRig']
            pref.prod_security = preferences['security']
            pref.prod_sub_facility = preferences['componentFacility']
            pref.prod_sub_me_rig = preferences['componentMeRig']
            pref.prod_sub_te_rig = preferences['componentTeRig']
            pref.prod_sub_security = preferences['componentSecurity']
            pref.prod_price_region_minerals = preferences['priceMineralRegion']
            pref.prod_price_type_minerals = preferences['priceMineralType']
            pref.prod_price_region_pi = preferences['pricePiRegion']
            pref.prod_price_type_pi = preferences['pricePiType']
            pref.prod_price_region_moongoo = preferences['priceMoongooRegion']
            pref.prod_price_type_moongoo = preferences['priceMoongooType']
            pref.prod_price_region_others = preferences['priceOtherRegion']
            pref.prod_price_type_others = preferences['priceOtherType']
            pref.prod_character_id = preferences['characterId']

            db.session.commit()

            check = check_main and check_sub
            return json_response(
                'success' if check else 'warning',
                ("Production preferences updated, solarsystem not updated "
                 "as the system does not exist or does not have any index."
                 if not check else
                 "Production preferences successfuly saved."),
                200
            )

        except:
            logger.exception('Cannot update preferences')
            db.session.rollback()
            return json_response('danger',
                                 'Error while updating preferences',
                                 500)
    else:
        return json_response('danger', 'Error: preferences are empty', 500)


def update_invention_preference(preferences):
    """ Called by update_user_industry_preference, update the invention
    preferences """
    if preferences:
        pref = current_user.pref

        try:
            solar_system, check = check_solar_system_name_index(
                preferences['system']
            )
            if check:
                pref.invention_system = solar_system

            pref.invention_facility = preferences['facility']
            pref.invention_invention_rig = preferences['inventionRig']
            pref.invention_copy_rig = preferences['copyRig']
            pref.invention_security = preferences['security']
            pref.invention_price_region = preferences['priceRegion']
            pref.invention_price_type = preferences['priceType']
            pref.invention_character_id = preferences['characterId']
            pref.invention_copy_implant = preferences['copyImplant']

            db.session.commit()
            return json_response(
                'success' if check else 'warning',
                ("Invention preferences updated, solarsystem not updated "
                 "as the system does not exist or does not have any index."
                 if not check else "Invention preferences successfuly saved."),
                200
            )

        except:
            logger.exception('Cannot update preferences')
            db.session.rollback()
            return json_response('danger',
                                 'Error while updating preferences',
                                 500)
    else:
        return json_response('danger', 'Error: preferences are empty', 500)


def update_research_preference(preferences):
    """ Called by update_user_industry_preference, update the research
    preferences """
    if preferences:
        pref = current_user.pref

        try:
            solar_system, check = check_solar_system_name_index(
                preferences['system']
            )
            if check:
                pref.research_system = solar_system

            pref.research_facility = preferences['facility']
            pref.research_me_rig = preferences['meRig']
            pref.research_te_rig = preferences['teRig']
            pref.research_copy_rig = preferences['copyRig']
            pref.research_security = preferences['security']
            pref.research_character_id = preferences['characterId']
            pref.research_me_implant = preferences['meImplant']
            pref.research_te_implant = preferences['teImplant']
            pref.research_copy_implant = preferences['copyImplant']

            db.session.commit()
            return json_response(
                'success' if check else 'warning',
                ("Research preferences updated, solarsystem not updated "
                 "as the system does not exist or does not have any index."
                 if not check else "Research preferences successfuly saved."),
                200
            )

        except:
            logger.exception('Cannot update preferences')
            db.session.rollback()
            return json_response('danger',
                                 'Error while updating preferences',
                                 500)
    else:
        return json_response('danger', 'Error: preferences are empty', 500)


def check_solar_system_name_index(system_name):
    """ Check if a solarsystem exists and return the real name from database
    (prevents lower/upper case issues) """
    system = SolarSystem.query.filter(
        func.lower(SolarSystem.name) == func.lower(system_name)
    ).one_or_none()

    if system:
        industry_indexes = IndustryIndex.query.filter(
            IndustryIndex.solarsystem_id == system.id,
        ).all()
        if industry_indexes:
            return system.name, True

    return 'Jita', False
