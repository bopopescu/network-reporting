(function($){

    var config = window.ToastjsConfig = {
        defaultTimeOut: 3000,
        position: ["top", "right"],
        notificationStyles: {
            padding: "12px 18px",
            margin: "0 0 6px 0",
            backgroundColor: "#000",
            opacity: 0.8,
            color: "#fff",
            font: "normal 13px 'Droid Sans', sans-serif",
            borderRadius: "3px",
            boxShadow: "#999 0 0 12px",
            width: "300px"
        },
        notificationStylesHover: {
            opacity: 1,
            boxShadow: "#000 0 0 12px"
        },
        container: $("<div></div>")
    };

    $(document).ready(function() {
        config.container.css("position", "absolute");
        config.container.css("z-index", 9999);
        config.container.css(config.position[0], "12px");
        config.container.css(config.position[1], "12px");
        $("body").append(config.container);
    });

    function getNotificationElement() {
        return $("<div>").css(config.notificationStyles).hover(function() {
            $(this).css(config.notificationStylesHover);
        }, function() {
            $(this).css(config.notificationStyles);
        });
    }

    var Toast = window.Toast = {};

    Toast.notify = function(message, title, iconUrl, timeOut) {
        var notificationElement = getNotificationElement();

        timeOut = timeOut || config.defaultTimeOut;

        if (iconUrl) {
            var iconElement = $("<img/>", {
                src: iconUrl,
                css: {
                    width: 36,
                    height: 36,
                    display: "inline-block",
                    verticalAlign: "middle"
                }
            });
            notificationElement.append(iconElement);
        }

        var textElement = $("<div/>").css({
            display: 'inline-block',
            verticalAlign: 'middle',
            padding: '0 12px'
        });

        if (title) {
            var titleElement = $("<div/>");
            titleElement.append(document.createTextNode(title));
            titleElement.css("font-weight", "bold");
            textElement.append(titleElement);
        }

        if (message) {
            var messageElement = $("<div/>");
            messageElement.append(document.createTextNode(message));
            textElement.append(messageElement);
        }

        notificationElement.delay(timeOut).fadeOut(function(){
            notificationElement.remove();
        });
        notificationElement.bind("click", function() {
            notificationElement.hide();
        });

        notificationElement.append(textElement);
        config.container.prepend(notificationElement);
    };

    Toast.info = function(message, title) {
        Toast.notify(message, title, "");
    };

    Toast.warning = function(message, title) {
        Toast.notify(message, title, "");
    };

    Toast.error = function(message, title) {
        Toast.notify(message, title, "/images/36x36-error.png");
    };

    Toast.success = function(message, title) {
        Toast.notify(message, title, "/images/36x36-success.png");
    };

}(this.jQuery));
