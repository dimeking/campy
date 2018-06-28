from google.appengine.ext import ndb

import json, logging

class UserInfo(ndb.Model):
    email_id = ndb.StringProperty(required=True)
    name = ndb.JsonProperty(required=True)
    preferences = ndb.JsonProperty(compressed=False)

class PropertyInfo(ndb.Model):
    id = ndb.StringProperty(required=True)
    details = ndb.JsonProperty(compressed=False)
    available_dates = ndb.JsonProperty(compressed=False)
    
class UserPropertyInfo(ndb.Model):
    email_id = ndb.StringProperty(required=True)
    property_list = ndb.JsonProperty(compressed=False)
    

def save_user_info(email_id, name, preferences):
    # do not store or update to empty if or refresh token
    if not email_id or not name or not preferences:
        return False

    try:
        # look for user id
        users = UserInfo.query(UserInfo.email_id == email_id).fetch()

        # if no entry then create
        if not any(users):
            user = UserInfo()
            user.email_id = email_id            
            user.name = name
            user.preferences = preferences            
            user.put()
            print "email id: ", user.email_id
            print "user name: ", user.name
            print "user preferences: ", user.preferences
            return True

        # update if found and different
        update = False
        user = users[0]
        if user.name != name:
            user.name = name
            update = True
        if user.preferences != preferences:
            user.preferences = preferences
            update = True
        if update:
            user.put()
            print "email id: ", user.email_id
            print "user name: ", user.name
            print "user preferences: ", user.preferences
    except Exception:
        logging.exception('Exception occured during save_user_info.')
        return False

    return True

def get_user_info(email_id):
    try:
        # look for user id    
        users = UserInfo.query(UserInfo.email_id == email_id).fetch()
    except Exception:
        logging.exception('Exception occured during get_user_info.')
        return {}    

    return users[0].name, users[0].preferences if any(users) else {}


def save_property_details(property_id, property_details):
    # do not store or update to empty if or refresh token
    if not property_id or not property_details:
        return False

    try:
        # look for property id
        properties = PropertyInfo.query(PropertyInfo.id == property_id).fetch()

        # if no entry then create
        if not any(properties):
            prop = PropertyInfo()
            prop.id = property_id            
            prop.details = property_details   
            prop.put()
            print "property_details: ", prop.details
            return True

        # update if found and different
        prop = properties[0]
        if prop.details != property_details:
            prop.details = property_details
            prop.put()
            print "property_details: ", prop.details

    except Exception:
        logging.exception('Exception occured during save_property_details.')
        return False

    return True

def save_property_dates(property_id, available_dates):
    # do not store or update to empty if or refresh token
    if not property_id or not available_dates:
        return False

    try:
        # look for property id
        properties = PropertyInfo.query(PropertyInfo.id == property_id).fetch()

        # if no entry then create
        if not any(properties):
            prop = PropertyInfo()
            prop.id = property_id            
            prop.available_dates = available_dates   
            prop.put()
            print "property_id: ", prop.id
            print "available_dates: ", prop.available_dates
            return True

        # update if found and different
        prop = properties[0]
        if not prop.available_dates:
            prop.available_dates = {}
        for day in available_dates.keys():
            if day not in prop.available_dates or not prop.available_dates[day]:
                prop.available_dates[day] = [] 
            if prop.available_dates[day] != available_dates[day]:
                prop.available_dates[day] = available_dates[day]
                prop.put()
                print "property_id: ", prop.id
                print "available_dates: ", prop.available_dates

    except Exception:
        logging.exception('Exception occured during save_property_dates.')
        return False

    return True

def get_property_details(property_id):
    try:
        # look for property id
        properties = PropertyInfo.query(PropertyInfo.id == property_id).fetch()
    except Exception:
        logging.exception('Exception occured during get_property_details.')
        return {}    

    return properties[0].details if any(properties) and properties[0].details else {}

def get_properties(num=100):
    try:
        # look for property id
        properties = PropertyInfo.query().fetch(num)
    except Exception:
        logging.exception('Exception occured during get_properties.')
        return []    

    return [prop.id for prop in properties]

def get_property_available_dates(property_id):
    try:
        # look for property id
        properties = PropertyInfo.query(PropertyInfo.id == property_id).fetch()
    except Exception:
        logging.exception('Exception occured during get_property_available_dates.')
        return {}    

    return properties[0].available_dates if any(properties) and properties[0].available_dates else {}


def save_user_property(email_id, property_id):
    # do not store or update to empty if or refresh token
    if not email_id or not property_id:
        return False

    print "property_id: ", property_id
    try:
        # look for user id
        properties = UserPropertyInfo.query(UserPropertyInfo.email_id == email_id).fetch()

        # if no entry then create
        if not any(properties):
            prop = UserPropertyInfo()
            prop.email_id = email_id  
            prop.property_list = [property_id]    
            prop.put()
            print "email_id: ", email_id
            print "property_list: ", prop.property_list                          
            return True

        # update if found and different
        prop = properties[0]
        if not prop.property_list:
            prop.property_list = []      
        if property_id not in prop.property_list:
            prop.property_list.append(property_id)
            prop.put()
            print "email_id: ", email_id
            print "property_list: ", prop.property_list            
    except Exception:
        logging.exception('Exception occured during save_user_property.')
        return False

    return True

def get_user_properties(email_id):
    print "get_user_properties::email_id: ", email_id
    
    try:
        # look for user id    
        properties = UserPropertyInfo.query(UserPropertyInfo.email_id == email_id).fetch()
    except Exception:
        logging.exception('Exception occured during get_user_properties.')
        return []    
    
    return properties[0].property_list if any(properties) and properties[0].property_list else []
    # print "get_user_properties::property_list: ", property_list

