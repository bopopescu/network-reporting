SUBSCRIBED_BUNDLE = 76031836593; // topic_name, topic, username
SHARED_BUNDLE = 78027206593; // {"actor":"Jim", "topic": "Berkshire", "topic_name":"bh", "title":"Awesome stuff", "body":"cool!", "primary_dereferenced_url":"http://www.google.com", "username":"jpjpjp"}
HIGHNOTE_APP_KEY = "894742ed38e6a6f42f6b6b690ea57b2c";
HIGHNOTE_DEV_APP_KEY = "01dddada3a038e16fbb63076015424c9";
var highnote_fbConnected = false;

function highnote_messageAction(id, action_type, onComplete, params, body) {
	var ajaxRequest = new Ajax.Request("/action", {
	    method:       'post', 
	    parameters:   {"id": id, "action_type": action_type}, 
	    asynchronous: true,
	    onComplete:   function() {
			if (params) {
				if (action_type == "star" && params['show_share_dialog'] == 'True') {
					FB.Connect.showFeedDialog(SHARED_BUNDLE, params, body);
				}
			}
			onComplete();
		}
	});
	return false;
}

function highnote_messageReverseAction(id, action_type, onComplete) {
	var ajaxRequest = new Ajax.Request("/action/reverse", {
	    method:       'post', 
	    parameters:   {"id": id, "action_type": action_type}, 
	    asynchronous: true,
	    onComplete:   onComplete
	});
	return false;
}

function highnote_pageAction(id, action_type, q, onComplete) {
	var ajaxRequest = new Ajax.Request("/action/page", {
	    method:       'post', 
	    parameters:   {"id": id, "action_type": action_type, "q": q}, 
	    asynchronous: true,
	    onComplete:   onComplete
	});
	return false;
}

function highnote_focus_textarea(e) {
	if (!e.clickedIt) {
	e.value = '';
	e.rows = 3;
	e.style.color = "#222";
	e.clickedIt = true;
}
}

function highnote_publishSubscribedAction(user_id, p) {
	FB.Connect.showFeedDialog(SUBSCRIBED_BUNDLE, p);
}

function highnote_loadFacebook(connected_method, not_connected_method) {
	FB.init(location.port > 1000 ? HIGHNOTE_DEV_APP_KEY : HIGHNOTE_APP_KEY, "/connect/xd_receiver.html",
		{"ifUserConnected":connected_method,  "ifUserNotConnected":not_connected_method});
}

function highnote_showConnectedBox(user_id) {
	highnote_fbConnected = true;
	if ($('not_connected_box') != null) {
		$('not_connected_box').hide();
	}
	if ($('connected_box') != null) {
		$('connected_box').show();
	}
}

function highnote_showNotConnectedBox() {
	highnote_fbConnected = false;
	if ($('connected_box') != null) {
		$('connected_box').hide();
	}
	if ($('not_connected_box') != null) {
		$('not_connected_box').show();
	}
}

function facebook_connect_friends() {
	return FB.Connect.inviteConnectUsers();
}

function facebook_find_friends() {
	FB.Facebook.apiClient.friends_getAppUsers(function(result) {
		alert(result);
	});	
}

function onYouTubePlayerReady(playerid) {
	ytplayer = $('player_' + playerid);
	if (ytplayer) {
	  ytplayer.playVideo();
	}
}

Number.prototype.mod = function(n) {
return ((this%n)+n)%n;
}

