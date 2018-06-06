from google.appengine.ext import ndb

import json, logging

class UserInfo(ndb.Model):
    email_id = ndb.StringProperty(required=True)
    name = ndb.JsonProperty(required=True)
    preferences = ndb.JsonProperty(compressed=False)

class TrackingInfo(ndb.Model):
    email_id = ndb.StringProperty(required=True)
    tracker_list = ndb.JsonProperty(compressed=False)
    tracked_info = ndb.JsonProperty(compressed=False)
    

def store_user_info(email_id, name, preferences):
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
        if user.name != json.dumps(name):
            user.name = json.dumps(name)
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
        logging.exception('Exception occured during store_user_info.')
        return False

    return True

def get_user_info(email_id):
    try:
        # look for user id    
        users = UserInfo.query(UserInfo.email_id == email_id).fetch()
    except Exception:
        logging.exception('Exception occured during get_user_info.')
        return None    

    return users[0].name, users[0].preferences if any(users) else None


def store_tracker_item(email_id, tracker_item):
    # do not store or update to empty if or refresh token
    if not email_id or not tracker_item:
        return False

    print "tracker_item: ", tracker_item
    try:
        # look for user id
        trackers = TrackingInfo.query(TrackingInfo.email_id == email_id).fetch()

        # if no entry then create
        if not any(trackers):
            tracker = TrackingInfo()
            tracker.email_id = email_id  
            tracker_items = [tracker_item]   
            tracker.tracker_list = tracker_items    
            tracker.put()
            print "email_id: ", email_id
            print "tracker_list: ", tracker.tracker_list                          
            return True

        # update if found and different
        tracker = trackers[0]
        tracker_items = tracker.tracker_list       
        print "tracker_items: ", tracker_items        
        matched_items = [item for item in tracker_items if tracker_item['id'] in item]
        if not any(matched_items):
            tracker_items.append(tracker_item)
            tracker.tracker_list = tracker_items       
            tracker.put()
            print "tracker_list: ", tracker.tracker_list            
    except Exception:
        logging.exception('Exception occured during store_tracker_item.')
        return False

    return True

def get_tracker_list(email_id):
    print "get_tracker_list::email_id: ", email_id
    
    try:
        # look for user id    
        trackers = TrackingInfo.query(TrackingInfo.email_id == email_id).fetch()
    except Exception:
        logging.exception('Exception occured during get_tracked_info.')
        return []    
    
    tracker_list = trackers[0].tracker_list if any(trackers) else []
    print "get_tracker_list::tracker_list: ", tracker_list
    return tracker_list
    # return { 'email_id': trackers[0].email_id, 'tracker_list': json.load(trackers[0].tracker_list) } if any(trackers) else None

def store_tracked_info(email_id, tracked_info):
    # do not store or update to empty if or refresh token
    if not email_id or not tracked_info:
        return False

    try:
        # look for user id
        trackers = TrackingInfo.query(TrackingInfo.email_id == email_id).fetch()

        # if no entry then create
        if not any(trackers):
            tracker = TrackingInfo()
            tracker.email_id = email_id  
            tracker.tracked_info = tracked_info       
            tracker.put()
            print "tracked_info: ", tracker.tracked_info
            
            return True

        # update if found and different
        tracker = trackers[0]
        if tracker.tracked_info != tracked_info:
            tracker.tracked_info = tracked_info       
            tracker.put()
            # print "tracked_info: ", tracker.tracked_info
            
    except Exception:
        logging.exception('Exception occured during store_tracked_info.')
        return False

    return True

def get_tracked_info(email_id):
    try:
        # look for user id    
        trackers = TrackingInfo.query(TrackingInfo.email_id == email_id).fetch()
    except Exception:
        logging.exception('Exception occured during get_tracked_info.')
        return None    

    return trackers[0].tracked_info if any(trackers) else None
    # return { 'email_id': trackers[0].email_id, 'tracked_info': json.load(trackers[0].tracked_info) } if any(trackers) else None

