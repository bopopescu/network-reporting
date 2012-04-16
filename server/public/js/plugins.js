// Underscore.js 1.2.0
// (c) 2011 Jeremy Ashkenas, DocumentCloud Inc.
// Underscore is freely distributable under the MIT license.
// Portions of Underscore are inspired or borrowed from Prototype,
// Oliver Steele's Functional, and John Resig's Micro-Templating.
// For all details and documentation:
// http://documentcloud.github.com/underscore
(function(){function q(a,c,d){if(a===c)return a!==0||1/a==1/c;if(a==null)return a===c;var e=typeof a;if(e!=typeof c)return false;if(!a!=!c)return false;if(b.isNaN(a))return b.isNaN(c);var f=b.isString(a),g=b.isString(c);if(f||g)return f&&g&&String(a)==String(c);f=b.isNumber(a);g=b.isNumber(c);if(f||g)return f&&g&&+a==+c;f=b.isBoolean(a);g=b.isBoolean(c);if(f||g)return f&&g&&+a==+c;f=b.isDate(a);g=b.isDate(c);if(f||g)return f&&g&&a.getTime()==c.getTime();f=b.isRegExp(a);g=b.isRegExp(c);if(f||g)return f&&
g&&a.source==c.source&&a.global==c.global&&a.multiline==c.multiline&&a.ignoreCase==c.ignoreCase;if(e!="object")return false;if(a._chain)a=a._wrapped;if(c._chain)c=c._wrapped;if(b.isFunction(a.isEqual))return a.isEqual(c);for(e=d.length;e--;)if(d[e]==a)return true;d.push(a);e=0;f=true;if(a.length===+a.length||c.length===+c.length){if(e=a.length,f=e==c.length)for(;e--;)if(!(f=e in a==e in c&&q(a[e],c[e],d)))break}else{for(var h in a)if(l.call(a,h)&&(e++,!(f=l.call(c,h)&&q(a[h],c[h],d))))break;if(f){for(h in c)if(l.call(c,
h)&&!e--)break;f=!e}}d.pop();return f}var r=this,F=r._,n={},k=Array.prototype,o=Object.prototype,i=k.slice,G=k.unshift,u=o.toString,l=o.hasOwnProperty,v=k.forEach,w=k.map,x=k.reduce,y=k.reduceRight,z=k.filter,A=k.every,B=k.some,p=k.indexOf,C=k.lastIndexOf,o=Array.isArray,H=Object.keys,s=Function.prototype.bind,b=function(a){return new m(a)};typeof module!=="undefined"&&module.exports?(module.exports=b,b._=b):r._=b;b.VERSION="1.2.0";var j=b.each=b.forEach=function(a,c,b){if(a!=null)if(v&&a.forEach===
v)a.forEach(c,b);else if(a.length===+a.length)for(var e=0,f=a.length;e<f;e++){if(e in a&&c.call(b,a[e],e,a)===n)break}else for(e in a)if(l.call(a,e)&&c.call(b,a[e],e,a)===n)break};b.map=function(a,c,b){var e=[];if(a==null)return e;if(w&&a.map===w)return a.map(c,b);j(a,function(a,g,h){e[e.length]=c.call(b,a,g,h)});return e};b.reduce=b.foldl=b.inject=function(a,c,d,e){var f=d!==void 0;a==null&&(a=[]);if(x&&a.reduce===x)return e&&(c=b.bind(c,e)),f?a.reduce(c,d):a.reduce(c);j(a,function(a,b,i){f?d=c.call(e,
d,a,b,i):(d=a,f=true)});if(!f)throw new TypeError("Reduce of empty array with no initial value");return d};b.reduceRight=b.foldr=function(a,c,d,e){a==null&&(a=[]);if(y&&a.reduceRight===y)return e&&(c=b.bind(c,e)),d!==void 0?a.reduceRight(c,d):a.reduceRight(c);a=(b.isArray(a)?a.slice():b.toArray(a)).reverse();return b.reduce(a,c,d,e)};b.find=b.detect=function(a,c,b){var e;D(a,function(a,g,h){if(c.call(b,a,g,h))return e=a,true});return e};b.filter=b.select=function(a,c,b){var e=[];if(a==null)return e;
if(z&&a.filter===z)return a.filter(c,b);j(a,function(a,g,h){c.call(b,a,g,h)&&(e[e.length]=a)});return e};b.reject=function(a,c,b){var e=[];if(a==null)return e;j(a,function(a,g,h){c.call(b,a,g,h)||(e[e.length]=a)});return e};b.every=b.all=function(a,c,b){var e=true;if(a==null)return e;if(A&&a.every===A)return a.every(c,b);j(a,function(a,g,h){if(!(e=e&&c.call(b,a,g,h)))return n});return e};var D=b.some=b.any=function(a,c,d){var c=c||b.identity,e=false;if(a==null)return e;if(B&&a.some===B)return a.some(c,
d);j(a,function(a,b,h){if(e|=c.call(d,a,b,h))return n});return!!e};b.include=b.contains=function(a,c){var b=false;if(a==null)return b;if(p&&a.indexOf===p)return a.indexOf(c)!=-1;D(a,function(a){if(b=a===c)return true});return b};b.invoke=function(a,c){var d=i.call(arguments,2);return b.map(a,function(a){return(c.call?c||a:a[c]).apply(a,d)})};b.pluck=function(a,c){return b.map(a,function(a){return a[c]})};b.max=function(a,c,d){if(!c&&b.isArray(a))return Math.max.apply(Math,a);if(!c&&b.isEmpty(a))return-Infinity;
var e={computed:-Infinity};j(a,function(a,b,h){b=c?c.call(d,a,b,h):a;b>=e.computed&&(e={value:a,computed:b})});return e.value};b.min=function(a,c,d){if(!c&&b.isArray(a))return Math.min.apply(Math,a);if(!c&&b.isEmpty(a))return Infinity;var e={computed:Infinity};j(a,function(a,b,h){b=c?c.call(d,a,b,h):a;b<e.computed&&(e={value:a,computed:b})});return e.value};b.shuffle=function(a){var c=[],b;j(a,function(a,f){f==0?c[0]=a:(b=Math.floor(Math.random()*(f+1)),c[f]=c[b],c[b]=a)});return c};b.sortBy=function(a,
c,d){return b.pluck(b.map(a,function(a,b,g){return{value:a,criteria:c.call(d,a,b,g)}}).sort(function(a,b){var c=a.criteria,d=b.criteria;return c<d?-1:c>d?1:0}),"value")};b.groupBy=function(a,b){var d={};j(a,function(a,f){var g=b(a,f);(d[g]||(d[g]=[])).push(a)});return d};b.sortedIndex=function(a,c,d){d||(d=b.identity);for(var e=0,f=a.length;e<f;){var g=e+f>>1;d(a[g])<d(c)?e=g+1:f=g}return e};b.toArray=function(a){return!a?[]:a.toArray?a.toArray():b.isArray(a)?i.call(a):b.isArguments(a)?i.call(a):
b.values(a)};b.size=function(a){return b.toArray(a).length};b.first=b.head=function(a,b,d){return b!=null&&!d?i.call(a,0,b):a[0]};b.initial=function(a,b,d){return i.call(a,0,a.length-(b==null||d?1:b))};b.last=function(a,b,d){return b!=null&&!d?i.call(a,a.length-b):a[a.length-1]};b.rest=b.tail=function(a,b,d){return i.call(a,b==null||d?1:b)};b.compact=function(a){return b.filter(a,function(a){return!!a})};b.flatten=function(a){return b.reduce(a,function(a,d){if(b.isArray(d))return a.concat(b.flatten(d));
a[a.length]=d;return a},[])};b.without=function(a){return b.difference(a,i.call(arguments,1))};b.uniq=b.unique=function(a,c,d){var d=d?b.map(a,d):a,e=[];b.reduce(d,function(d,g,h){if(0==h||(c===true?b.last(d)!=g:!b.include(d,g)))d[d.length]=g,e[e.length]=a[h];return d},[]);return e};b.union=function(){return b.uniq(b.flatten(arguments))};b.intersection=b.intersect=function(a){var c=i.call(arguments,1);return b.filter(b.uniq(a),function(a){return b.every(c,function(c){return b.indexOf(c,a)>=0})})};
b.difference=function(a,c){return b.filter(a,function(a){return!b.include(c,a)})};b.zip=function(){for(var a=i.call(arguments),c=b.max(b.pluck(a,"length")),d=Array(c),e=0;e<c;e++)d[e]=b.pluck(a,""+e);return d};b.indexOf=function(a,c,d){if(a==null)return-1;var e;if(d)return d=b.sortedIndex(a,c),a[d]===c?d:-1;if(p&&a.indexOf===p)return a.indexOf(c);for(d=0,e=a.length;d<e;d++)if(a[d]===c)return d;return-1};b.lastIndexOf=function(a,b){if(a==null)return-1;if(C&&a.lastIndexOf===C)return a.lastIndexOf(b);
for(var d=a.length;d--;)if(a[d]===b)return d;return-1};b.range=function(a,b,d){arguments.length<=1&&(b=a||0,a=0);for(var d=arguments[2]||1,e=Math.max(Math.ceil((b-a)/d),0),f=0,g=Array(e);f<e;)g[f++]=a,a+=d;return g};b.bind=function(a,b){if(a.bind===s&&s)return s.apply(a,i.call(arguments,1));var d=i.call(arguments,2);return function(){return a.apply(b,d.concat(i.call(arguments)))}};b.bindAll=function(a){var c=i.call(arguments,1);c.length==0&&(c=b.functions(a));j(c,function(c){a[c]=b.bind(a[c],a)});
return a};b.memoize=function(a,c){var d={};c||(c=b.identity);return function(){var b=c.apply(this,arguments);return l.call(d,b)?d[b]:d[b]=a.apply(this,arguments)}};b.delay=function(a,b){var d=i.call(arguments,2);return setTimeout(function(){return a.apply(a,d)},b)};b.defer=function(a){return b.delay.apply(b,[a,1].concat(i.call(arguments,1)))};var E=function(a,b,d){var e;return function(){var f=this,g=arguments,h=function(){e=null;a.apply(f,g)};d&&clearTimeout(e);if(d||!e)e=setTimeout(h,b)}};b.throttle=
function(a,b){return E(a,b,false)};b.debounce=function(a,b){return E(a,b,true)};b.once=function(a){var b=false,d;return function(){if(b)return d;b=true;return d=a.apply(this,arguments)}};b.wrap=function(a,b){return function(){var d=[a].concat(i.call(arguments));return b.apply(this,d)}};b.compose=function(){var a=i.call(arguments);return function(){for(var b=i.call(arguments),d=a.length-1;d>=0;d--)b=[a[d].apply(this,b)];return b[0]}};b.after=function(a,b){return function(){if(--a<1)return b.apply(this,
arguments)}};b.keys=H||function(a){if(a!==Object(a))throw new TypeError("Invalid object");var b=[],d;for(d in a)l.call(a,d)&&(b[b.length]=d);return b};b.values=function(a){return b.map(a,b.identity)};b.functions=b.methods=function(a){var c=[],d;for(d in a)b.isFunction(a[d])&&c.push(d);return c.sort()};b.extend=function(a){j(i.call(arguments,1),function(b){for(var d in b)b[d]!==void 0&&(a[d]=b[d])});return a};b.defaults=function(a){j(i.call(arguments,1),function(b){for(var d in b)a[d]==null&&(a[d]=
b[d])});return a};b.clone=function(a){return b.isArray(a)?a.slice():b.extend({},a)};b.tap=function(a,b){b(a);return a};b.isEqual=function(a,b){return q(a,b,[])};b.isEmpty=function(a){if(b.isArray(a)||b.isString(a))return a.length===0;for(var c in a)if(l.call(a,c))return false;return true};b.isElement=function(a){return!!(a&&a.nodeType==1)};b.isArray=o||function(a){return u.call(a)==="[object Array]"};b.isObject=function(a){return a===Object(a)};b.isArguments=function(a){return!(!a||!l.call(a,"callee"))};
b.isFunction=function(a){return!(!a||!a.constructor||!a.call||!a.apply)};b.isString=function(a){return!!(a===""||a&&a.charCodeAt&&a.substr)};b.isNumber=function(a){return!!(a===0||a&&a.toExponential&&a.toFixed)};b.isNaN=function(a){return a!==a};b.isBoolean=function(a){return a===true||a===false||u.call(a)=="[object Boolean]"};b.isDate=function(a){return!(!a||!a.getTimezoneOffset||!a.setUTCFullYear)};b.isRegExp=function(a){return!(!a||!a.test||!a.exec||!(a.ignoreCase||a.ignoreCase===false))};b.isNull=
function(a){return a===null};b.isUndefined=function(a){return a===void 0};b.noConflict=function(){r._=F;return this};b.identity=function(a){return a};b.times=function(a,b,d){for(var e=0;e<a;e++)b.call(d,e)};b.escape=function(a){return(""+a).replace(/&(?!\w+;|#\d+;|#x[\da-f]+;)/gi,"&amp;").replace(/</g,"&lt;").replace(/>/g,"&gt;").replace(/"/g,"&quot;").replace(/'/g,"&#x27;").replace(/\//g,"&#x2F;")};b.mixin=function(a){j(b.functions(a),function(c){I(c,b[c]=a[c])})};var J=0;b.uniqueId=function(a){var b=
J++;return a?a+b:b};b.templateSettings={evaluate:/<%([\s\S]+?)%>/g,interpolate:/<%=([\s\S]+?)%>/g,escape:/<%-([\s\S]+?)%>/g};b.template=function(a,c){var d=b.templateSettings,d="var __p=[],print=function(){__p.push.apply(__p,arguments);};with(obj||{}){__p.push('"+a.replace(/\\/g,"\\\\").replace(/'/g,"\\'").replace(d.escape,function(a,b){return"',_.escape("+b.replace(/\\'/g,"'")+"),'"}).replace(d.interpolate,function(a,b){return"',"+b.replace(/\\'/g,"'")+",'"}).replace(d.evaluate||null,function(a,
b){return"');"+b.replace(/\\'/g,"'").replace(/[\r\n\t]/g," ")+"__p.push('"}).replace(/\r/g,"\\r").replace(/\n/g,"\\n").replace(/\t/g,"\\t")+"');}return __p.join('');",d=new Function("obj",d);return c?d(c):d};var m=function(a){this._wrapped=a};b.prototype=m.prototype;var t=function(a,c){return c?b(a).chain():a},I=function(a,c){m.prototype[a]=function(){var a=i.call(arguments);G.call(a,this._wrapped);return t(c.apply(b,a),this._chain)}};b.mixin(b);j("pop,push,reverse,shift,sort,splice,unshift".split(","),
function(a){var b=k[a];m.prototype[a]=function(){b.apply(this._wrapped,arguments);return t(this._wrapped,this._chain)}});j(["concat","join","slice"],function(a){var b=k[a];m.prototype[a]=function(){return t(b.apply(this._wrapped,arguments),this._chain)}});m.prototype.chain=function(){this._chain=true;return this};m.prototype.value=function(){return this._wrapped}})();
/*
    http://www.JSON.org/json2.js
    2011-02-23

    Public Domain.

    NO WARRANTY EXPRESSED OR IMPLIED. USE AT YOUR OWN RISK.

    See http://www.JSON.org/js.html


    This code should be minified before deployment.
    See http://javascript.crockford.com/jsmin.html

    USE YOUR OWN COPY. IT IS EXTREMELY UNWISE TO LOAD CODE FROM SERVERS YOU DO
    NOT CONTROL.


    This file creates a global JSON object containing two methods: stringify
    and parse.

        JSON.stringify(value, replacer, space)
            value       any JavaScript value, usually an object or array.

            replacer    an optional parameter that determines how object
                        values are stringified for objects. It can be a
                        function or an array of strings.

            space       an optional parameter that specifies the indentation
                        of nested structures. If it is omitted, the text will
                        be packed without extra whitespace. If it is a number,
                        it will specify the number of spaces to indent at each
                        level. If it is a string (such as '\t' or '&nbsp;'),
                        it contains the characters used to indent at each level.

            This method produces a JSON text from a JavaScript value.

            When an object value is found, if the object contains a toJSON
            method, its toJSON method will be called and the result will be
            stringified. A toJSON method does not serialize: it returns the
            value represented by the name/value pair that should be serialized,
            or undefined if nothing should be serialized. The toJSON method
            will be passed the key associated with the value, and this will be
            bound to the value

            For example, this would serialize Dates as ISO strings.

                Date.prototype.toJSON = function (key) {
                    function f(n) {
                        // Format integers to have at least two digits.
                        return n < 10 ? '0' + n : n;
                    }

                    return this.getUTCFullYear()   + '-' +
                         f(this.getUTCMonth() + 1) + '-' +
                         f(this.getUTCDate())      + 'T' +
                         f(this.getUTCHours())     + ':' +
                         f(this.getUTCMinutes())   + ':' +
                         f(this.getUTCSeconds())   + 'Z';
                };

            You can provide an optional replacer method. It will be passed the
            key and value of each member, with this bound to the containing
            object. The value that is returned from your method will be
            serialized. If your method returns undefined, then the member will
            be excluded from the serialization.

            If the replacer parameter is an array of strings, then it will be
            used to select the members to be serialized. It filters the results
            such that only members with keys listed in the replacer array are
            stringified.

            Values that do not have JSON representations, such as undefined or
            functions, will not be serialized. Such values in objects will be
            dropped; in arrays they will be replaced with null. You can use
            a replacer function to replace those with JSON values.
            JSON.stringify(undefined) returns undefined.

            The optional space parameter produces a stringification of the
            value that is filled with line breaks and indentation to make it
            easier to read.

            If the space parameter is a non-empty string, then that string will
            be used for indentation. If the space parameter is a number, then
            the indentation will be that many spaces.

            Example:

            text = JSON.stringify(['e', {pluribus: 'unum'}]);
            // text is '["e",{"pluribus":"unum"}]'


            text = JSON.stringify(['e', {pluribus: 'unum'}], null, '\t');
            // text is '[\n\t"e",\n\t{\n\t\t"pluribus": "unum"\n\t}\n]'

            text = JSON.stringify([new Date()], function (key, value) {
                return this[key] instanceof Date ?
                    'Date(' + this[key] + ')' : value;
            });
            // text is '["Date(---current time---)"]'


        JSON.parse(text, reviver)
            This method parses a JSON text to produce an object or array.
            It can throw a SyntaxError exception.

            The optional reviver parameter is a function that can filter and
            transform the results. It receives each of the keys and values,
            and its return value is used instead of the original value.
            If it returns what it received, then the structure is not modified.
            If it returns undefined then the member is deleted.

            Example:

            // Parse the text. Values that look like ISO date strings will
            // be converted to Date objects.

            myData = JSON.parse(text, function (key, value) {
                var a;
                if (typeof value === 'string') {
                    a =
/^(\d{4})-(\d{2})-(\d{2})T(\d{2}):(\d{2}):(\d{2}(?:\.\d*)?)Z$/.exec(value);
                    if (a) {
                        return new Date(Date.UTC(+a[1], +a[2] - 1, +a[3], +a[4],
                            +a[5], +a[6]));
                    }
                }
                return value;
            });

            myData = JSON.parse('["Date(09/09/2001)"]', function (key, value) {
                var d;
                if (typeof value === 'string' &&
                        value.slice(0, 5) === 'Date(' &&
                        value.slice(-1) === ')') {
                    d = new Date(value.slice(5, -1));
                    if (d) {
                        return d;
                    }
                }
                return value;
            });


    This is a reference implementation. You are free to copy, modify, or
    redistribute.
*/

/*jslint evil: true, strict: false, regexp: false */

/*members "", "\b", "\t", "\n", "\f", "\r", "\"", JSON, "\\", apply,
    call, charCodeAt, getUTCDate, getUTCFullYear, getUTCHours,
    getUTCMinutes, getUTCMonth, getUTCSeconds, hasOwnProperty, join,
    lastIndex, length, parse, prototype, push, replace, slice, stringify,
    test, toJSON, toString, valueOf
*/


// Create a JSON object only if one does not already exist. We create the
// methods in a closure to avoid creating global variables.

var JSON;
if (!JSON) {
    JSON = {};
}

(function () {
    "use strict";

    function f(n) {
        // Format integers to have at least two digits.
        return n < 10 ? '0' + n : n;
    }

    if (typeof Date.prototype.toJSON !== 'function') {

        Date.prototype.toJSON = function (key) {

            return isFinite(this.valueOf()) ?
                this.getUTCFullYear()     + '-' +
                f(this.getUTCMonth() + 1) + '-' +
                f(this.getUTCDate())      + 'T' +
                f(this.getUTCHours())     + ':' +
                f(this.getUTCMinutes())   + ':' +
                f(this.getUTCSeconds())   + 'Z' : null;
        };

        String.prototype.toJSON      =
            Number.prototype.toJSON  =
            Boolean.prototype.toJSON = function (key) {
                return this.valueOf();
            };
    }

    var cx = /[\u0000\u00ad\u0600-\u0604\u070f\u17b4\u17b5\u200c-\u200f\u2028-\u202f\u2060-\u206f\ufeff\ufff0-\uffff]/g,
        escapable = /[\\\"\x00-\x1f\x7f-\x9f\u00ad\u0600-\u0604\u070f\u17b4\u17b5\u200c-\u200f\u2028-\u202f\u2060-\u206f\ufeff\ufff0-\uffff]/g,
        gap,
        indent,
        meta = {    // table of character substitutions
            '\b': '\\b',
            '\t': '\\t',
            '\n': '\\n',
            '\f': '\\f',
            '\r': '\\r',
            '"' : '\\"',
            '\\': '\\\\'
        },
        rep;


    function quote(string) {

// If the string contains no control characters, no quote characters, and no
// backslash characters, then we can safely slap some quotes around it.
// Otherwise we must also replace the offending characters with safe escape
// sequences.

        escapable.lastIndex = 0;
        return escapable.test(string) ? '"' + string.replace(escapable, function (a) {
            var c = meta[a];
            return typeof c === 'string' ? c :
                '\\u' + ('0000' + a.charCodeAt(0).toString(16)).slice(-4);
        }) + '"' : '"' + string + '"';
    }


    function str(key, holder) {

// Produce a string from holder[key].

        var i,          // The loop counter.
            k,          // The member key.
            v,          // The member value.
            length,
            mind = gap,
            partial,
            value = holder[key];

// If the value has a toJSON method, call it to obtain a replacement value.

        if (value && typeof value === 'object' &&
                typeof value.toJSON === 'function') {
            value = value.toJSON(key);
        }

// If we were called with a replacer function, then call the replacer to
// obtain a replacement value.

        if (typeof rep === 'function') {
            value = rep.call(holder, key, value);
        }

// What happens next depends on the value's type.

        switch (typeof value) {
        case 'string':
            return quote(value);

        case 'number':

// JSON numbers must be finite. Encode non-finite numbers as null.

            return isFinite(value) ? String(value) : 'null';

        case 'boolean':
        case 'null':

// If the value is a boolean or null, convert it to a string. Note:
// typeof null does not produce 'null'. The case is included here in
// the remote chance that this gets fixed someday.

            return String(value);

// If the type is 'object', we might be dealing with an object or an array or
// null.

        case 'object':

// Due to a specification blunder in ECMAScript, typeof null is 'object',
// so watch out for that case.

            if (!value) {
                return 'null';
            }

// Make an array to hold the partial results of stringifying this object value.

            gap += indent;
            partial = [];

// Is the value an array?

            if (Object.prototype.toString.apply(value) === '[object Array]') {

// The value is an array. Stringify every element. Use null as a placeholder
// for non-JSON values.

                length = value.length;
                for (i = 0; i < length; i += 1) {
                    partial[i] = str(i, value) || 'null';
                }

// Join all of the elements together, separated with commas, and wrap them in
// brackets.

                v = partial.length === 0 ? '[]' : gap ?
                    '[\n' + gap + partial.join(',\n' + gap) + '\n' + mind + ']' :
                    '[' + partial.join(',') + ']';
                gap = mind;
                return v;
            }

// If the replacer is an array, use it to select the members to be stringified.

            if (rep && typeof rep === 'object') {
                length = rep.length;
                for (i = 0; i < length; i += 1) {
                    if (typeof rep[i] === 'string') {
                        k = rep[i];
                        v = str(k, value);
                        if (v) {
                            partial.push(quote(k) + (gap ? ': ' : ':') + v);
                        }
                    }
                }
            } else {

// Otherwise, iterate through all of the keys in the object.

                for (k in value) {
                    if (Object.prototype.hasOwnProperty.call(value, k)) {
                        v = str(k, value);
                        if (v) {
                            partial.push(quote(k) + (gap ? ': ' : ':') + v);
                        }
                    }
                }
            }

// Join all of the member texts together, separated with commas,
// and wrap them in braces.

            v = partial.length === 0 ? '{}' : gap ?
                '{\n' + gap + partial.join(',\n' + gap) + '\n' + mind + '}' :
                '{' + partial.join(',') + '}';
            gap = mind;
            return v;
        }
    }

// If the JSON object does not yet have a stringify method, give it one.

    if (typeof JSON.stringify !== 'function') {
        JSON.stringify = function (value, replacer, space) {

// The stringify method takes a value and an optional replacer, and an optional
// space parameter, and returns a JSON text. The replacer can be a function
// that can replace values, or an array of strings that will select the keys.
// A default replacer method can be provided. Use of the space parameter can
// produce text that is more easily readable.

            var i;
            gap = '';
            indent = '';

// If the space parameter is a number, make an indent string containing that
// many spaces.

            if (typeof space === 'number') {
                for (i = 0; i < space; i += 1) {
                    indent += ' ';
                }

// If the space parameter is a string, it will be used as the indent string.

            } else if (typeof space === 'string') {
                indent = space;
            }

// If there is a replacer, it must be a function or an array.
// Otherwise, throw an error.

            rep = replacer;
            if (replacer && typeof replacer !== 'function' &&
                    (typeof replacer !== 'object' ||
                    typeof replacer.length !== 'number')) {
                throw new Error('JSON.stringify');
            }

// Make a fake root object containing our value under the key of ''.
// Return the result of stringifying the value.

            return str('', {'': value});
        };
    }


// If the JSON object does not yet have a parse method, give it one.

    if (typeof JSON.parse !== 'function') {
        JSON.parse = function (text, reviver) {

// The parse method takes a text and an optional reviver function, and returns
// a JavaScript value if the text is a valid JSON text.

            var j;

            function walk(holder, key) {

// The walk method is used to recursively walk the resulting structure so
// that modifications can be made.

                var k, v, value = holder[key];
                if (value && typeof value === 'object') {
                    for (k in value) {
                        if (Object.prototype.hasOwnProperty.call(value, k)) {
                            v = walk(value, k);
                            if (v !== undefined) {
                                value[k] = v;
                            } else {
                                delete value[k];
                            }
                        }
                    }
                }
                return reviver.call(holder, key, value);
            }


// Parsing happens in four stages. In the first stage, we replace certain
// Unicode characters with escape sequences. JavaScript handles many characters
// incorrectly, either silently deleting them, or treating them as line endings.

            text = String(text);
            cx.lastIndex = 0;
            if (cx.test(text)) {
                text = text.replace(cx, function (a) {
                    return '\\u' +
                        ('0000' + a.charCodeAt(0).toString(16)).slice(-4);
                });
            }

// In the second stage, we run the text against regular expressions that look
// for non-JSON patterns. We are especially concerned with '()' and 'new'
// because they can cause invocation, and '=' because it can cause mutation.
// But just to be safe, we want to reject all unexpected forms.

// We split the second stage into 4 regexp operations in order to work around
// crippling inefficiencies in IE's and Safari's regexp engines. First we
// replace the JSON backslash pairs with '@' (a non-JSON character). Second, we
// replace all simple value tokens with ']' characters. Third, we delete all
// open brackets that follow a colon or comma or that begin the text. Finally,
// we look to see that the remaining characters are only whitespace or ']' or
// ',' or ':' or '{' or '}'. If that is so, then the text is safe for eval.

            if (/^[\],:{}\s]*$/
                    .test(text.replace(/\\(?:["\\\/bfnrt]|u[0-9a-fA-F]{4})/g, '@')
                        .replace(/"[^"\\\n\r]*"|true|false|null|-?\d+(?:\.\d*)?(?:[eE][+\-]?\d+)?/g, ']')
                        .replace(/(?:^|:|,)(?:\s*\[)+/g, ''))) {

// In the third stage we use the eval function to compile the text into a
// JavaScript structure. The '{' operator is subject to a syntactic ambiguity
// in JavaScript: it can begin a block or an object literal. We wrap the text
// in parens to eliminate the ambiguity.

                j = eval('(' + text + ')');

// In the optional fourth stage, we recursively walk the new structure, passing
// each name/value pair to a reviver function for possible transformation.

                return typeof reviver === 'function' ?
                    walk({'': j}, '') : j;
            }

// If the text is not JSON parseable, then a SyntaxError is thrown.

            throw new SyntaxError('JSON.parse');
        };
    }
}());
// Backbone.js 0.5.3
// (c) 2010 Jeremy Ashkenas, DocumentCloud Inc.
// Backbone may be freely distributed under the MIT license.
// For all details and documentation:
// http://documentcloud.github.com/backbone
/*
 * @depends underscore.min.js
 * @depends json2.js
 */
(function(){var h=this,p=h.Backbone,e;e=typeof exports!=="undefined"?exports:h.Backbone={};e.VERSION="0.5.3";var f=h._;if(!f&&typeof require!=="undefined")f=require("underscore")._;var g=h.jQuery||h.Zepto;e.noConflict=function(){h.Backbone=p;return this};e.emulateHTTP=!1;e.emulateJSON=!1;e.Events={bind:function(a,b,c){var d=this._callbacks||(this._callbacks={});(d[a]||(d[a]=[])).push([b,c]);return this},unbind:function(a,b){var c;if(a){if(c=this._callbacks)if(b){c=c[a];if(!c)return this;for(var d=
0,e=c.length;d<e;d++)if(c[d]&&b===c[d][0]){c[d]=null;break}}else c[a]=[]}else this._callbacks={};return this},trigger:function(a){var b,c,d,e,f=2;if(!(c=this._callbacks))return this;for(;f--;)if(b=f?a:"all",b=c[b])for(var g=0,h=b.length;g<h;g++)(d=b[g])?(e=f?Array.prototype.slice.call(arguments,1):arguments,d[0].apply(d[1]||this,e)):(b.splice(g,1),g--,h--);return this}};e.Model=function(a,b){var c;a||(a={});if(c=this.defaults)f.isFunction(c)&&(c=c.call(this)),a=f.extend({},c,a);this.attributes={};
this._escapedAttributes={};this.cid=f.uniqueId("c");this.set(a,{silent:!0});this._changed=!1;this._previousAttributes=f.clone(this.attributes);if(b&&b.collection)this.collection=b.collection;this.initialize(a,b)};f.extend(e.Model.prototype,e.Events,{_previousAttributes:null,_changed:!1,idAttribute:"id",initialize:function(){},toJSON:function(){return f.clone(this.attributes)},get:function(a){return this.attributes[a]},escape:function(a){var b;if(b=this._escapedAttributes[a])return b;b=this.attributes[a];
return this._escapedAttributes[a]=(b==null?"":""+b).replace(/&(?!\w+;|#\d+;|#x[\da-f]+;)/gi,"&amp;").replace(/</g,"&lt;").replace(/>/g,"&gt;").replace(/"/g,"&quot;").replace(/'/g,"&#x27;").replace(/\//g,"&#x2F;")},has:function(a){return this.attributes[a]!=null},set:function(a,b){b||(b={});if(!a)return this;if(a.attributes)a=a.attributes;var c=this.attributes,d=this._escapedAttributes;if(!b.silent&&this.validate&&!this._performValidation(a,b))return!1;if(this.idAttribute in a)this.id=a[this.idAttribute];
var e=this._changing;this._changing=!0;for(var g in a){var h=a[g];if(!f.isEqual(c[g],h))c[g]=h,delete d[g],this._changed=!0,b.silent||this.trigger("change:"+g,this,h,b)}!e&&!b.silent&&this._changed&&this.change(b);this._changing=!1;return this},unset:function(a,b){if(!(a in this.attributes))return this;b||(b={});var c={};c[a]=void 0;if(!b.silent&&this.validate&&!this._performValidation(c,b))return!1;delete this.attributes[a];delete this._escapedAttributes[a];a==this.idAttribute&&delete this.id;this._changed=
!0;b.silent||(this.trigger("change:"+a,this,void 0,b),this.change(b));return this},clear:function(a){a||(a={});var b,c=this.attributes,d={};for(b in c)d[b]=void 0;if(!a.silent&&this.validate&&!this._performValidation(d,a))return!1;this.attributes={};this._escapedAttributes={};this._changed=!0;if(!a.silent){for(b in c)this.trigger("change:"+b,this,void 0,a);this.change(a)}return this},fetch:function(a){a||(a={});var b=this,c=a.success;a.success=function(d,e,f){if(!b.set(b.parse(d,f),a))return!1;c&&
c(b,d)};a.error=i(a.error,b,a);return(this.sync||e.sync).call(this,"read",this,a)},save:function(a,b){b||(b={});if(a&&!this.set(a,b))return!1;var c=this,d=b.success;b.success=function(a,e,f){if(!c.set(c.parse(a,f),b))return!1;d&&d(c,a,f)};b.error=i(b.error,c,b);var f=this.isNew()?"create":"update";return(this.sync||e.sync).call(this,f,this,b)},destroy:function(a){a||(a={});if(this.isNew())return this.trigger("destroy",this,this.collection,a);var b=this,c=a.success;a.success=function(d){b.trigger("destroy",
b,b.collection,a);c&&c(b,d)};a.error=i(a.error,b,a);return(this.sync||e.sync).call(this,"delete",this,a)},url:function(){var a=k(this.collection)||this.urlRoot||l();if(this.isNew())return a;return a+(a.charAt(a.length-1)=="/"?"":"/")+encodeURIComponent(this.id)},parse:function(a){return a},clone:function(){return new this.constructor(this)},isNew:function(){return this.id==null},change:function(a){this.trigger("change",this,a);this._previousAttributes=f.clone(this.attributes);this._changed=!1},hasChanged:function(a){if(a)return this._previousAttributes[a]!=
this.attributes[a];return this._changed},changedAttributes:function(a){a||(a=this.attributes);var b=this._previousAttributes,c=!1,d;for(d in a)f.isEqual(b[d],a[d])||(c=c||{},c[d]=a[d]);return c},previous:function(a){if(!a||!this._previousAttributes)return null;return this._previousAttributes[a]},previousAttributes:function(){return f.clone(this._previousAttributes)},_performValidation:function(a,b){var c=this.validate(a);if(c)return b.error?b.error(this,c,b):this.trigger("error",this,c,b),!1;return!0}});
e.Collection=function(a,b){b||(b={});if(b.comparator)this.comparator=b.comparator;f.bindAll(this,"_onModelEvent","_removeReference");this._reset();a&&this.reset(a,{silent:!0});this.initialize.apply(this,arguments)};f.extend(e.Collection.prototype,e.Events,{model:e.Model,initialize:function(){},toJSON:function(){return this.map(function(a){return a.toJSON()})},add:function(a,b){if(f.isArray(a))for(var c=0,d=a.length;c<d;c++)this._add(a[c],b);else this._add(a,b);return this},remove:function(a,b){if(f.isArray(a))for(var c=
0,d=a.length;c<d;c++)this._remove(a[c],b);else this._remove(a,b);return this},get:function(a){if(a==null)return null;return this._byId[a.id!=null?a.id:a]},getByCid:function(a){return a&&this._byCid[a.cid||a]},at:function(a){return this.models[a]},sort:function(a){a||(a={});if(!this.comparator)throw Error("Cannot sort a set without a comparator");this.models=this.sortBy(this.comparator);a.silent||this.trigger("reset",this,a);return this},pluck:function(a){return f.map(this.models,function(b){return b.get(a)})},
reset:function(a,b){a||(a=[]);b||(b={});this.each(this._removeReference);this._reset();this.add(a,{silent:!0});b.silent||this.trigger("reset",this,b);return this},fetch:function(a){a||(a={});var b=this,c=a.success;a.success=function(d,f,e){b[a.add?"add":"reset"](b.parse(d,e),a);c&&c(b,d)};a.error=i(a.error,b,a);return(this.sync||e.sync).call(this,"read",this,a)},create:function(a,b){var c=this;b||(b={});a=this._prepareModel(a,b);if(!a)return!1;var d=b.success;b.success=function(a,e,f){c.add(a,b);
d&&d(a,e,f)};a.save(null,b);return a},parse:function(a){return a},chain:function(){return f(this.models).chain()},_reset:function(){this.length=0;this.models=[];this._byId={};this._byCid={}},_prepareModel:function(a,b){if(a instanceof e.Model){if(!a.collection)a.collection=this}else{var c=a;a=new this.model(c,{collection:this});a.validate&&!a._performValidation(c,b)&&(a=!1)}return a},_add:function(a,b){b||(b={});a=this._prepareModel(a,b);if(!a)return!1;var c=this.getByCid(a);if(c)throw Error(["Can't add the same model to a set twice",
c.id]);this._byId[a.id]=a;this._byCid[a.cid]=a;this.models.splice(b.at!=null?b.at:this.comparator?this.sortedIndex(a,this.comparator):this.length,0,a);a.bind("all",this._onModelEvent);this.length++;b.silent||a.trigger("add",a,this,b);return a},_remove:function(a,b){b||(b={});a=this.getByCid(a)||this.get(a);if(!a)return null;delete this._byId[a.id];delete this._byCid[a.cid];this.models.splice(this.indexOf(a),1);this.length--;b.silent||a.trigger("remove",a,this,b);this._removeReference(a);return a},
_removeReference:function(a){this==a.collection&&delete a.collection;a.unbind("all",this._onModelEvent)},_onModelEvent:function(a,b,c,d){(a=="add"||a=="remove")&&c!=this||(a=="destroy"&&this._remove(b,d),b&&a==="change:"+b.idAttribute&&(delete this._byId[b.previous(b.idAttribute)],this._byId[b.id]=b),this.trigger.apply(this,arguments))}});f.each(["forEach","each","map","reduce","reduceRight","find","detect","filter","select","reject","every","all","some","any","include","contains","invoke","max",
"min","sortBy","sortedIndex","toArray","size","first","rest","last","without","indexOf","lastIndexOf","isEmpty","groupBy"],function(a){e.Collection.prototype[a]=function(){return f[a].apply(f,[this.models].concat(f.toArray(arguments)))}});e.Router=function(a){a||(a={});if(a.routes)this.routes=a.routes;this._bindRoutes();this.initialize.apply(this,arguments)};var q=/:([\w\d]+)/g,r=/\*([\w\d]+)/g,s=/[-[\]{}()+?.,\\^$|#\s]/g;f.extend(e.Router.prototype,e.Events,{initialize:function(){},route:function(a,
b,c){e.history||(e.history=new e.History);f.isRegExp(a)||(a=this._routeToRegExp(a));e.history.route(a,f.bind(function(d){d=this._extractParameters(a,d);c.apply(this,d);this.trigger.apply(this,["route:"+b].concat(d))},this))},navigate:function(a,b){e.history.navigate(a,b)},_bindRoutes:function(){if(this.routes){var a=[],b;for(b in this.routes)a.unshift([b,this.routes[b]]);b=0;for(var c=a.length;b<c;b++)this.route(a[b][0],a[b][1],this[a[b][1]])}},_routeToRegExp:function(a){a=a.replace(s,"\\$&").replace(q,
"([^/]*)").replace(r,"(.*?)");return RegExp("^"+a+"$")},_extractParameters:function(a,b){return a.exec(b).slice(1)}});e.History=function(){this.handlers=[];f.bindAll(this,"checkUrl")};var j=/^#*/,t=/msie [\w.]+/,m=!1;f.extend(e.History.prototype,{interval:50,getFragment:function(a,b){if(a==null)if(this._hasPushState||b){a=window.location.pathname;var c=window.location.search;c&&(a+=c);a.indexOf(this.options.root)==0&&(a=a.substr(this.options.root.length))}else a=window.location.hash;return decodeURIComponent(a.replace(j,
""))},start:function(a){if(m)throw Error("Backbone.history has already been started");this.options=f.extend({},{root:"/"},this.options,a);this._wantsPushState=!!this.options.pushState;this._hasPushState=!(!this.options.pushState||!window.history||!window.history.pushState);a=this.getFragment();var b=document.documentMode;if(b=t.exec(navigator.userAgent.toLowerCase())&&(!b||b<=7))this.iframe=g('<iframe src="javascript:0" tabindex="-1" />').hide().appendTo("body")[0].contentWindow,this.navigate(a);
this._hasPushState?g(window).bind("popstate",this.checkUrl):"onhashchange"in window&&!b?g(window).bind("hashchange",this.checkUrl):setInterval(this.checkUrl,this.interval);this.fragment=a;m=!0;a=window.location;b=a.pathname==this.options.root;if(this._wantsPushState&&!this._hasPushState&&!b)return this.fragment=this.getFragment(null,!0),window.location.replace(this.options.root+"#"+this.fragment),!0;else if(this._wantsPushState&&this._hasPushState&&b&&a.hash)this.fragment=a.hash.replace(j,""),window.history.replaceState({},
document.title,a.protocol+"//"+a.host+this.options.root+this.fragment);if(!this.options.silent)return this.loadUrl()},route:function(a,b){this.handlers.unshift({route:a,callback:b})},checkUrl:function(){var a=this.getFragment();a==this.fragment&&this.iframe&&(a=this.getFragment(this.iframe.location.hash));if(a==this.fragment||a==decodeURIComponent(this.fragment))return!1;this.iframe&&this.navigate(a);this.loadUrl()||this.loadUrl(window.location.hash)},loadUrl:function(a){var b=this.fragment=this.getFragment(a);
return f.any(this.handlers,function(a){if(a.route.test(b))return a.callback(b),!0})},navigate:function(a,b){var c=(a||"").replace(j,"");if(!(this.fragment==c||this.fragment==decodeURIComponent(c))){if(this._hasPushState){var d=window.location;c.indexOf(this.options.root)!=0&&(c=this.options.root+c);this.fragment=c;window.history.pushState({},document.title,d.protocol+"//"+d.host+c)}else if(window.location.hash=this.fragment=c,this.iframe&&c!=this.getFragment(this.iframe.location.hash))this.iframe.document.open().close(),
this.iframe.location.hash=c;b&&this.loadUrl(a)}}});e.View=function(a){this.cid=f.uniqueId("view");this._configure(a||{});this._ensureElement();this.delegateEvents();this.initialize.apply(this,arguments)};var u=/^(\S+)\s*(.*)$/,n=["model","collection","el","id","attributes","className","tagName"];f.extend(e.View.prototype,e.Events,{tagName:"div",$:function(a){return g(a,this.el)},initialize:function(){},render:function(){return this},remove:function(){g(this.el).remove();return this},make:function(a,
b,c){a=document.createElement(a);b&&g(a).attr(b);c&&g(a).html(c);return a},delegateEvents:function(a){if(a||(a=this.events))for(var b in f.isFunction(a)&&(a=a.call(this)),g(this.el).unbind(".delegateEvents"+this.cid),a){var c=this[a[b]];if(!c)throw Error('Event "'+a[b]+'" does not exist');var d=b.match(u),e=d[1];d=d[2];c=f.bind(c,this);e+=".delegateEvents"+this.cid;d===""?g(this.el).bind(e,c):g(this.el).delegate(d,e,c)}},_configure:function(a){this.options&&(a=f.extend({},this.options,a));for(var b=
0,c=n.length;b<c;b++){var d=n[b];a[d]&&(this[d]=a[d])}this.options=a},_ensureElement:function(){if(this.el){if(f.isString(this.el))this.el=g(this.el).get(0)}else{var a=this.attributes||{};if(this.id)a.id=this.id;if(this.className)a["class"]=this.className;this.el=this.make(this.tagName,a)}}});e.Model.extend=e.Collection.extend=e.Router.extend=e.View.extend=function(a,b){var c=v(this,a,b);c.extend=this.extend;return c};var w={create:"POST",update:"PUT","delete":"DELETE",read:"GET"};e.sync=function(a,
b,c){var d=w[a];c=f.extend({type:d,dataType:"json"},c);if(!c.url)c.url=k(b)||l();if(!c.data&&b&&(a=="create"||a=="update"))c.contentType="application/json",c.data=JSON.stringify(b.toJSON());if(e.emulateJSON)c.contentType="application/x-www-form-urlencoded",c.data=c.data?{model:c.data}:{};if(e.emulateHTTP&&(d==="PUT"||d==="DELETE")){if(e.emulateJSON)c.data._method=d;c.type="POST";c.beforeSend=function(a){a.setRequestHeader("X-HTTP-Method-Override",d)}}if(c.type!=="GET"&&!e.emulateJSON)c.processData=
!1;return g.ajax(c)};var o=function(){},v=function(a,b,c){var d;d=b&&b.hasOwnProperty("constructor")?b.constructor:function(){return a.apply(this,arguments)};f.extend(d,a);o.prototype=a.prototype;d.prototype=new o;b&&f.extend(d.prototype,b);c&&f.extend(d,c);d.prototype.constructor=d;d.__super__=a.prototype;return d},k=function(a){if(!a||!a.url)return null;return f.isFunction(a.url)?a.url():a.url},l=function(){throw Error('A "url" property or function must be specified');},i=function(a,b,c){return function(d){a?
a(b,d,c):b.trigger("error",b,d,c)}}}).call(this);
/* =========================================================
 * bootstrap-datepicker.js 
 * http://www.eyecon.ro/bootstrap-datepicker
 * =========================================================
 * Copyright 2012 Stefan Petre
 *
 * Licensed under the Apache License, Version 2.0 (the "License");
 * you may not use this file except in compliance with the License.
 * You may obtain a copy of the License at
 *
 * http://www.apache.org/licenses/LICENSE-2.0
 *
 * Unless required by applicable law or agreed to in writing, software
 * distributed under the License is distributed on an "AS IS" BASIS,
 * WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
 * See the License for the specific language governing permissions and
 * limitations under the License.
 * ========================================================= */
 
!function( $ ) {
	
	// Picker object
	
	var Datepicker = function(element, options){
		this.element = $(element);
		this.format = DPGlobal.parseFormat(options.format||this.element.data('date-format')||'mm/dd/yyyy');
		this.picker = $(DPGlobal.template)
							.appendTo('body')
							.on({
								click: $.proxy(this.click, this),
								mousedown: $.proxy(this.mousedown, this)
							});
		this.isInput = this.element.is('input');
		this.component = this.element.is('.date') ? this.element.find('.add-on') : false;
		
		if (this.isInput) {
			this.element.on({
				focus: $.proxy(this.show, this),
				blur: $.proxy(this.hide, this),
				keyup: $.proxy(this.update, this)
			});
		} else {
			if (this.component){
				this.component.on('click', $.proxy(this.show, this));
			} else {
				this.element.on('click', $.proxy(this.show, this));
			}
		}
		
		this.viewMode = 0;
		this.weekStart = options.weekStart||this.element.data('date-weekstart')||0;
		this.weekEnd = this.weekStart == 0 ? 6 : this.weekStart - 1;
		this.fillDow();
		this.fillMonths();
		this.update();
		this.showMode();
	};
	
	Datepicker.prototype = {
		constructor: Datepicker,
		
		show: function(e) {
			this.picker.show();
			this.height = this.component ? this.component.outerHeight() : this.element.outerHeight();
			this.place();
			$(window).on('resize', $.proxy(this.place, this));
			if (e ) {
				e.stopPropagation();
				e.preventDefault();
			}
			if (!this.isInput) {
				$(document).on('mousedown', $.proxy(this.hide, this));
			}
			this.element.trigger({
				type: 'show',
				date: this.date
			});
		},
		
		hide: function(){
			this.picker.hide();
			$(window).off('resize', this.place);
			this.viewMode = 0;
			this.showMode();
			if (!this.isInput) {
				$(document).off('mousedown', this.hide);
			}
			this.setValue();
			this.element.trigger({
				type: 'hide',
				date: this.date
			});
		},
		
		setValue: function() {
			var formated = DPGlobal.formatDate(this.date, this.format);
			if (!this.isInput) {
				if (this.component){
					this.element.find('input').prop('value', formated);
				}
				this.element.data('date', formated);
			} else {
				this.element.prop('value', formated);
			}
		},
		
		place: function(){
			var offset = this.component ? this.component.offset() : this.element.offset();
			this.picker.css({
				top: offset.top + this.height,
				left: offset.left
			});
		},
		
		update: function(){
			this.date = DPGlobal.parseDate(
				this.isInput ? this.element.prop('value') : this.element.data('date'),
				this.format
			);
			this.viewDate = new Date(this.date);
			this.fill();
		},
		
		fillDow: function(){
			var dowCnt = this.weekStart;
			var html = '<tr>';
			while (dowCnt < this.weekStart + 7) {
				html += '<th class="dow">'+DPGlobal.dates.daysMin[(dowCnt++)%7]+'</th>';
			}
			html += '</tr>';
			this.picker.find('.datepicker-days thead').append(html);
		},
		
		fillMonths: function(){
			var html = '';
			var i = 0
			while (i < 12) {
				html += '<span class="month">'+DPGlobal.dates.monthsShort[i++]+'</span>';
			}
			this.picker.find('.datepicker-months td').append(html);
		},
		
		fill: function() {
			var d = new Date(this.viewDate),
				year = d.getFullYear(),
				month = d.getMonth(),
				currentDate = this.date.valueOf();
			this.picker.find('.datepicker-days th:eq(1)')
						.text(DPGlobal.dates.months[month]+' '+year);
			var prevMonth = new Date(year, month-1, 28,0,0,0,0),
				day = DPGlobal.getDaysInMonth(prevMonth.getFullYear(), prevMonth.getMonth());
			prevMonth.setDate(day);
			prevMonth.setDate(day - (prevMonth.getDay() - this.weekStart + 7)%7);
			var nextMonth = new Date(prevMonth);
			nextMonth.setDate(nextMonth.getDate() + 42);
			nextMonth = nextMonth.valueOf();
			html = [];
			var clsName;
			while(prevMonth.valueOf() < nextMonth) {
				if (prevMonth.getDay() == this.weekStart) {
					html.push('<tr>');
				}
				clsName = '';
				if (prevMonth.getMonth() < month) {
					clsName += ' old';
				} else if (prevMonth.getMonth() > month) {
					clsName += ' new';
				}
				if (prevMonth.valueOf() == currentDate) {
					clsName += ' active';
				}
				html.push('<td class="day'+clsName+'">'+prevMonth.getDate() + '</td>');
				if (prevMonth.getDay() == this.weekEnd) {
					html.push('</tr>');
				}
				prevMonth.setDate(prevMonth.getDate()+1);
			}
			this.picker.find('.datepicker-days tbody').empty().append(html.join(''));
			var currentYear = this.date.getFullYear();
			
			var months = this.picker.find('.datepicker-months')
						.find('th:eq(1)')
							.text(year)
							.end()
						.find('span').removeClass('active');
			if (currentYear == year) {
				months.eq(this.date.getMonth()).addClass('active');
			}
			
			html = '';
			year = parseInt(year/10, 10) * 10;
			var yearCont = this.picker.find('.datepicker-years')
								.find('th:eq(1)')
									.text(year + '-' + (year + 9))
									.end()
								.find('td');
			year -= 1;
			for (var i = -1; i < 11; i++) {
				html += '<span class="year'+(i == -1 || i == 10 ? ' old' : '')+(currentYear == year ? ' active' : '')+'">'+year+'</span>';
				year += 1;
			}
			yearCont.html(html);
		},
		
		click: function(e) {
			e.stopPropagation();
			e.preventDefault();
			var target = $(e.target).closest('span, td, th');
			if (target.length == 1) {
				switch(target[0].nodeName.toLowerCase()) {
					case 'th':
						switch(target[0].className) {
							case 'switch':
								this.showMode(1);
								break;
							case 'prev':
							case 'next':
								this.viewDate['set'+DPGlobal.modes[this.viewMode].navFnc].call(
									this.viewDate,
									this.viewDate['get'+DPGlobal.modes[this.viewMode].navFnc].call(this.viewDate) + 
									DPGlobal.modes[this.viewMode].navStep * (target[0].className == 'prev' ? -1 : 1)
								);
								this.fill();
								break;
						}
						break;
					case 'span':
						if (target.is('.month')) {
							var month = target.parent().find('span').index(target);
							this.viewDate.setMonth(month);
						} else {
							var year = parseInt(target.text(), 10)||0;
							this.viewDate.setFullYear(year);
						}
						this.showMode(-1);
						this.fill();
						break;
					case 'td':
						if (target.is('.day')){
							var day = parseInt(target.text(), 10)||1;
							var month = this.viewDate.getMonth();
							if (target.is('.old')) {
								month -= 1;
							} else if (target.is('.new')) {
								month += 1;
							}
							var year = this.viewDate.getFullYear();
							this.date = new Date(year, month, day,0,0,0,0);
							this.viewDate = new Date(year, month, day,0,0,0,0);
							this.fill();
							this.setValue();
							this.element.trigger({
								type: 'changeDate',
								date: this.date
							});
						}
						break;
				}
			}
		},
		
		mousedown: function(e){
			e.stopPropagation();
			e.preventDefault();
		},
		
		showMode: function(dir) {
			if (dir) {
				this.viewMode = Math.max(0, Math.min(2, this.viewMode + dir));
			}
			this.picker.find('>div').hide().filter('.datepicker-'+DPGlobal.modes[this.viewMode].clsName).show();
		}
	};
	
	$.fn.datepicker = function ( option ) {
		return this.each(function () {
			var $this = $(this),
				data = $this.data('datepicker'),
				options = typeof option == 'object' && option;
			if (!data) {
				$this.data('datepicker', (data = new Datepicker(this, $.extend({}, $.fn.datepicker.defaults,options))));
			}
			if (typeof option == 'string') data[option]();
		});
	};

	$.fn.datepicker.defaults = {
	};
	$.fn.datepicker.Constructor = Datepicker;
	
	var DPGlobal = {
		modes: [
			{
				clsName: 'days',
				navFnc: 'Month',
				navStep: 1
			},
			{
				clsName: 'months',
				navFnc: 'FullYear',
				navStep: 1
			},
			{
				clsName: 'years',
				navFnc: 'FullYear',
				navStep: 10
		}],
		dates:{
			days: ["Sunday", "Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"],
			daysShort: ["Sun", "Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"],
			daysMin: ["Su", "Mo", "Tu", "We", "Th", "Fr", "Sa", "Su"],
			months: ["January", "February", "March", "April", "May", "June", "July", "August", "September", "October", "November", "December"],
			monthsShort: ["Jan", "Feb", "Mar", "Apr", "May", "Jun", "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"]
		},
		isLeapYear: function (year) {
			return (((year % 4 === 0) && (year % 100 !== 0)) || (year % 400 === 0))
		},
		getDaysInMonth: function (year, month) {
			return [31, (DPGlobal.isLeapYear(year) ? 29 : 28), 31, 30, 31, 30, 31, 31, 30, 31, 30, 31][month]
		},
		parseFormat: function(format){
			var separator = format.match(/[.\/-].*?/),
				parts = format.split(/\W+/);
			if (!separator || !parts || parts.length == 0){
				throw new Error("Invalid date format.");
			}
			return {separator: separator, parts: parts};
		},
		parseDate: function(date, format) {
			var parts = date.split(format.separator),
				date = new Date(1970, 1, 1, 0, 0, 0),
				val;
			if (parts.length == format.parts.length) {
				for (var i=0, cnt = format.parts.length; i < cnt; i++) {
					val = parseInt(parts[i], 10)||1;
					switch(format.parts[i]) {
						case 'dd':
						case 'd':
							date.setDate(val);
							break;
						case 'mm':
						case 'm':
							date.setMonth(val - 1);
							break;
						case 'yy':
							date.setFullYear(2000 + val);
							break;
						case 'yyyy':
							date.setFullYear(val);
							break;
					}
				}
			}
			return date;
		},
		formatDate: function(date, format){
			var val = {
				d: date.getDate(),
				m: date.getMonth() + 1,
				yy: date.getFullYear().toString().substring(2),
				yyyy: date.getFullYear()
			};
			val.dd = (val.d < 10 ? '0' : '') + val.d;
			val.mm = (val.m < 10 ? '0' : '') + val.m;
			var date = [];
			for (var i=0, cnt = format.parts.length; i < cnt; i++) {
				date.push(val[format.parts[i]]);
			}
			return date.join(format.separator);
		},
		headTemplate: '<thead>'+
							'<tr>'+
								'<th class="prev"><i class="icon-arrow-left"/></th>'+
								'<th colspan="5" class="switch"></th>'+
								'<th class="next"><i class="icon-arrow-right"/></th>'+
							'</tr>'+
						'</thead>',
		contTemplate: '<tbody><tr><td colspan="7"></td></tr></tbody>'
	};
	DPGlobal.template = '<div class="datepicker dropdown-menu">'+
							'<div class="datepicker-days">'+
								'<table class=" table-condensed">'+
									DPGlobal.headTemplate+
									'<tbody></tbody>'+
								'</table>'+
							'</div>'+
							'<div class="datepicker-months">'+
								'<table class="table-condensed">'+
									DPGlobal.headTemplate+
									DPGlobal.contTemplate+
								'</table>'+
							'</div>'+
							'<div class="datepicker-years">'+
								'<table class="table-condensed">'+
									DPGlobal.headTemplate+
									DPGlobal.contTemplate+
								'</table>'+
							'</div>'+
						'</div>';

}( window.jQuery )
/* ===================================================
 * bootstrap-transition.js v2.0.2
 * http://twitter.github.com/bootstrap/javascript.html#transitions
 * ===================================================
 * Copyright 2012 Twitter, Inc.
 *
 * Licensed under the Apache License, Version 2.0 (the "License");
 * you may not use this file except in compliance with the License.
 * You may obtain a copy of the License at
 *
 * http://www.apache.org/licenses/LICENSE-2.0
 *
 * Unless required by applicable law or agreed to in writing, software
 * distributed under the License is distributed on an "AS IS" BASIS,
 * WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
 * See the License for the specific language governing permissions and
 * limitations under the License.
 * ========================================================== */

!function( $ ) {

  $(function () {

    "use strict"

    /* CSS TRANSITION SUPPORT (https://gist.github.com/373874)
     * ======================================================= */

    $.support.transition = (function () {
      var thisBody = document.body || document.documentElement
        , thisStyle = thisBody.style
        , support = thisStyle.transition !== undefined || thisStyle.WebkitTransition !== undefined || thisStyle.MozTransition !== undefined || thisStyle.MsTransition !== undefined || thisStyle.OTransition !== undefined

      return support && {
        end: (function () {
          var transitionEnd = "TransitionEnd"
          if ( $.browser.webkit ) {
          	transitionEnd = "webkitTransitionEnd"
          } else if ( $.browser.mozilla ) {
          	transitionEnd = "transitionend"
          } else if ( $.browser.opera ) {
          	transitionEnd = "oTransitionEnd"
          }
          return transitionEnd
        }())
      }
    })()

  })

}( window.jQuery );/* ==========================================================
 * bootstrap-alert.js v2.0.2
 * http://twitter.github.com/bootstrap/javascript.html#alerts
 * ==========================================================
 * Copyright 2012 Twitter, Inc.
 *
 * Licensed under the Apache License, Version 2.0 (the "License");
 * you may not use this file except in compliance with the License.
 * You may obtain a copy of the License at
 *
 * http://www.apache.org/licenses/LICENSE-2.0
 *
 * Unless required by applicable law or agreed to in writing, software
 * distributed under the License is distributed on an "AS IS" BASIS,
 * WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
 * See the License for the specific language governing permissions and
 * limitations under the License.
 * ========================================================== */


!function( $ ){

  "use strict"

 /* ALERT CLASS DEFINITION
  * ====================== */

  var dismiss = '[data-dismiss="alert"]'
    , Alert = function ( el ) {
        $(el).on('click', dismiss, this.close)
      }

  Alert.prototype = {

    constructor: Alert

  , close: function ( e ) {
      var $this = $(this)
        , selector = $this.attr('data-target')
        , $parent

      if (!selector) {
        selector = $this.attr('href')
        selector = selector && selector.replace(/.*(?=#[^\s]*$)/, '') //strip for ie7
      }

      $parent = $(selector)
      $parent.trigger('close')

      e && e.preventDefault()

      $parent.length || ($parent = $this.hasClass('alert') ? $this : $this.parent())

      $parent
        .trigger('close')
        .removeClass('in')

      function removeElement() {
        $parent
          .trigger('closed')
          .remove()
      }

      $.support.transition && $parent.hasClass('fade') ?
        $parent.on($.support.transition.end, removeElement) :
        removeElement()
    }

  }


 /* ALERT PLUGIN DEFINITION
  * ======================= */

  $.fn.alert = function ( option ) {
    return this.each(function () {
      var $this = $(this)
        , data = $this.data('alert')
      if (!data) $this.data('alert', (data = new Alert(this)))
      if (typeof option == 'string') data[option].call($this)
    })
  }

  $.fn.alert.Constructor = Alert


 /* ALERT DATA-API
  * ============== */

  $(function () {
    $('body').on('click.alert.data-api', dismiss, Alert.prototype.close)
  })

}( window.jQuery );/* ============================================================
 * bootstrap-button.js v2.0.2
 * http://twitter.github.com/bootstrap/javascript.html#buttons
 * ============================================================
 * Copyright 2012 Twitter, Inc.
 *
 * Licensed under the Apache License, Version 2.0 (the "License");
 * you may not use this file except in compliance with the License.
 * You may obtain a copy of the License at
 *
 * http://www.apache.org/licenses/LICENSE-2.0
 *
 * Unless required by applicable law or agreed to in writing, software
 * distributed under the License is distributed on an "AS IS" BASIS,
 * WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
 * See the License for the specific language governing permissions and
 * limitations under the License.
 * ============================================================ */

!function( $ ){

  "use strict"

 /* BUTTON PUBLIC CLASS DEFINITION
  * ============================== */

  var Button = function ( element, options ) {
    this.$element = $(element)
    this.options = $.extend({}, $.fn.button.defaults, options)
  }

  Button.prototype = {

      constructor: Button

    , setState: function ( state ) {
        var d = 'disabled'
          , $el = this.$element
          , data = $el.data()
          , val = $el.is('input') ? 'val' : 'html'

        state = state + 'Text'
        data.resetText || $el.data('resetText', $el[val]())

        $el[val](data[state] || this.options[state])

        // push to event loop to allow forms to submit
        setTimeout(function () {
          state == 'loadingText' ?
            $el.addClass(d).attr(d, d) :
            $el.removeClass(d).removeAttr(d)
        }, 0)
      }

    , toggle: function () {
        var $parent = this.$element.parent('[data-toggle="buttons-radio"]')

        $parent && $parent
          .find('.active')
          .removeClass('active')

        this.$element.toggleClass('active')
      }

  }


 /* BUTTON PLUGIN DEFINITION
  * ======================== */

  $.fn.button = function ( option ) {
    return this.each(function () {
      var $this = $(this)
        , data = $this.data('button')
        , options = typeof option == 'object' && option
      if (!data) $this.data('button', (data = new Button(this, options)))
      if (option == 'toggle') data.toggle()
      else if (option) data.setState(option)
    })
  }

  $.fn.button.defaults = {
    loadingText: 'loading...'
  }

  $.fn.button.Constructor = Button


 /* BUTTON DATA-API
  * =============== */

  $(function () {
    $('body').on('click.button.data-api', '[data-toggle^=button]', function ( e ) {
      var $btn = $(e.target)
      if (!$btn.hasClass('btn')) $btn = $btn.closest('.btn')
      $btn.button('toggle')
    })
  })

}( window.jQuery );/* ==========================================================
 * bootstrap-carousel.js v2.0.2
 * http://twitter.github.com/bootstrap/javascript.html#carousel
 * ==========================================================
 * Copyright 2012 Twitter, Inc.
 *
 * Licensed under the Apache License, Version 2.0 (the "License");
 * you may not use this file except in compliance with the License.
 * You may obtain a copy of the License at
 *
 * http://www.apache.org/licenses/LICENSE-2.0
 *
 * Unless required by applicable law or agreed to in writing, software
 * distributed under the License is distributed on an "AS IS" BASIS,
 * WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
 * See the License for the specific language governing permissions and
 * limitations under the License.
 * ========================================================== */


!function( $ ){

  "use strict"

 /* CAROUSEL CLASS DEFINITION
  * ========================= */

  var Carousel = function (element, options) {
    this.$element = $(element)
    this.options = $.extend({}, $.fn.carousel.defaults, options)
    this.options.slide && this.slide(this.options.slide)
    this.options.pause == 'hover' && this.$element
      .on('mouseenter', $.proxy(this.pause, this))
      .on('mouseleave', $.proxy(this.cycle, this))
  }

  Carousel.prototype = {

    cycle: function () {
      this.interval = setInterval($.proxy(this.next, this), this.options.interval)
      return this
    }

  , to: function (pos) {
      var $active = this.$element.find('.active')
        , children = $active.parent().children()
        , activePos = children.index($active)
        , that = this

      if (pos > (children.length - 1) || pos < 0) return

      if (this.sliding) {
        return this.$element.one('slid', function () {
          that.to(pos)
        })
      }

      if (activePos == pos) {
        return this.pause().cycle()
      }

      return this.slide(pos > activePos ? 'next' : 'prev', $(children[pos]))
    }

  , pause: function () {
      clearInterval(this.interval)
      this.interval = null
      return this
    }

  , next: function () {
      if (this.sliding) return
      return this.slide('next')
    }

  , prev: function () {
      if (this.sliding) return
      return this.slide('prev')
    }

  , slide: function (type, next) {
      var $active = this.$element.find('.active')
        , $next = next || $active[type]()
        , isCycling = this.interval
        , direction = type == 'next' ? 'left' : 'right'
        , fallback  = type == 'next' ? 'first' : 'last'
        , that = this

      this.sliding = true

      isCycling && this.pause()

      $next = $next.length ? $next : this.$element.find('.item')[fallback]()

      if ($next.hasClass('active')) return

      if (!$.support.transition && this.$element.hasClass('slide')) {
        this.$element.trigger('slide')
        $active.removeClass('active')
        $next.addClass('active')
        this.sliding = false
        this.$element.trigger('slid')
      } else {
        $next.addClass(type)
        $next[0].offsetWidth // force reflow
        $active.addClass(direction)
        $next.addClass(direction)
        this.$element.trigger('slide')
        this.$element.one($.support.transition.end, function () {
          $next.removeClass([type, direction].join(' ')).addClass('active')
          $active.removeClass(['active', direction].join(' '))
          that.sliding = false
          setTimeout(function () { that.$element.trigger('slid') }, 0)
        })
      }

      isCycling && this.cycle()

      return this
    }

  }


 /* CAROUSEL PLUGIN DEFINITION
  * ========================== */

  $.fn.carousel = function ( option ) {
    return this.each(function () {
      var $this = $(this)
        , data = $this.data('carousel')
        , options = typeof option == 'object' && option
      if (!data) $this.data('carousel', (data = new Carousel(this, options)))
      if (typeof option == 'number') data.to(option)
      else if (typeof option == 'string' || (option = options.slide)) data[option]()
      else data.cycle()
    })
  }

  $.fn.carousel.defaults = {
    interval: 5000
  , pause: 'hover'
  }

  $.fn.carousel.Constructor = Carousel


 /* CAROUSEL DATA-API
  * ================= */

  $(function () {
    $('body').on('click.carousel.data-api', '[data-slide]', function ( e ) {
      var $this = $(this), href
        , $target = $($this.attr('data-target') || (href = $this.attr('href')) && href.replace(/.*(?=#[^\s]+$)/, '')) //strip for ie7
        , options = !$target.data('modal') && $.extend({}, $target.data(), $this.data())
      $target.carousel(options)
      e.preventDefault()
    })
  })

}( window.jQuery );/* =============================================================
 * bootstrap-collapse.js v2.0.2
 * http://twitter.github.com/bootstrap/javascript.html#collapse
 * =============================================================
 * Copyright 2012 Twitter, Inc.
 *
 * Licensed under the Apache License, Version 2.0 (the "License");
 * you may not use this file except in compliance with the License.
 * You may obtain a copy of the License at
 *
 * http://www.apache.org/licenses/LICENSE-2.0
 *
 * Unless required by applicable law or agreed to in writing, software
 * distributed under the License is distributed on an "AS IS" BASIS,
 * WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
 * See the License for the specific language governing permissions and
 * limitations under the License.
 * ============================================================ */

!function( $ ){

  "use strict"

  var Collapse = function ( element, options ) {
  	this.$element = $(element)
    this.options = $.extend({}, $.fn.collapse.defaults, options)

    if (this.options["parent"]) {
      this.$parent = $(this.options["parent"])
    }

    this.options.toggle && this.toggle()
  }

  Collapse.prototype = {

    constructor: Collapse

  , dimension: function () {
      var hasWidth = this.$element.hasClass('width')
      return hasWidth ? 'width' : 'height'
    }

  , show: function () {
      var dimension = this.dimension()
        , scroll = $.camelCase(['scroll', dimension].join('-'))
        , actives = this.$parent && this.$parent.find('.in')
        , hasData

      if (actives && actives.length) {
        hasData = actives.data('collapse')
        actives.collapse('hide')
        hasData || actives.data('collapse', null)
      }

      this.$element[dimension](0)
      this.transition('addClass', 'show', 'shown')
      this.$element[dimension](this.$element[0][scroll])

    }

  , hide: function () {
      var dimension = this.dimension()
      this.reset(this.$element[dimension]())
      this.transition('removeClass', 'hide', 'hidden')
      this.$element[dimension](0)
    }

  , reset: function ( size ) {
      var dimension = this.dimension()

      this.$element
        .removeClass('collapse')
        [dimension](size || 'auto')
        [0].offsetWidth

      this.$element[size ? 'addClass' : 'removeClass']('collapse')

      return this
    }

  , transition: function ( method, startEvent, completeEvent ) {
      var that = this
        , complete = function () {
            if (startEvent == 'show') that.reset()
            that.$element.trigger(completeEvent)
          }

      this.$element
        .trigger(startEvent)
        [method]('in')

      $.support.transition && this.$element.hasClass('collapse') ?
        this.$element.one($.support.transition.end, complete) :
        complete()
  	}

  , toggle: function () {
      this[this.$element.hasClass('in') ? 'hide' : 'show']()
  	}

  }

  /* COLLAPSIBLE PLUGIN DEFINITION
  * ============================== */

  $.fn.collapse = function ( option ) {
    return this.each(function () {
      var $this = $(this)
        , data = $this.data('collapse')
        , options = typeof option == 'object' && option
      if (!data) $this.data('collapse', (data = new Collapse(this, options)))
      if (typeof option == 'string') data[option]()
    })
  }

  $.fn.collapse.defaults = {
    toggle: true
  }

  $.fn.collapse.Constructor = Collapse


 /* COLLAPSIBLE DATA-API
  * ==================== */

  $(function () {
    $('body').on('click.collapse.data-api', '[data-toggle=collapse]', function ( e ) {
      var $this = $(this), href
        , target = $this.attr('data-target')
          || e.preventDefault()
          || (href = $this.attr('href')) && href.replace(/.*(?=#[^\s]+$)/, '') //strip for ie7
        , option = $(target).data('collapse') ? 'toggle' : $this.data()
      $(target).collapse(option)
    })
  })

}( window.jQuery );/* ============================================================
 * bootstrap-dropdown.js v2.0.2
 * http://twitter.github.com/bootstrap/javascript.html#dropdowns
 * ============================================================
 * Copyright 2012 Twitter, Inc.
 *
 * Licensed under the Apache License, Version 2.0 (the "License");
 * you may not use this file except in compliance with the License.
 * You may obtain a copy of the License at
 *
 * http://www.apache.org/licenses/LICENSE-2.0
 *
 * Unless required by applicable law or agreed to in writing, software
 * distributed under the License is distributed on an "AS IS" BASIS,
 * WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
 * See the License for the specific language governing permissions and
 * limitations under the License.
 * ============================================================ */


!function( $ ){

  "use strict"

 /* DROPDOWN CLASS DEFINITION
  * ========================= */

  var toggle = '[data-toggle="dropdown"]'
    , Dropdown = function ( element ) {
        var $el = $(element).on('click.dropdown.data-api', this.toggle)
        $('html').on('click.dropdown.data-api', function () {
          $el.parent().removeClass('open')
        })
      }

  Dropdown.prototype = {

    constructor: Dropdown

  , toggle: function ( e ) {
      var $this = $(this)
        , selector = $this.attr('data-target')
        , $parent
        , isActive

      if (!selector) {
        selector = $this.attr('href')
        selector = selector && selector.replace(/.*(?=#[^\s]*$)/, '') //strip for ie7
      }

      $parent = $(selector)
      $parent.length || ($parent = $this.parent())

      isActive = $parent.hasClass('open')

      clearMenus()
      !isActive && $parent.toggleClass('open')

      return false
    }

  }

  function clearMenus() {
    $(toggle).parent().removeClass('open')
  }


  /* DROPDOWN PLUGIN DEFINITION
   * ========================== */

  $.fn.dropdown = function ( option ) {
    return this.each(function () {
      var $this = $(this)
        , data = $this.data('dropdown')
      if (!data) $this.data('dropdown', (data = new Dropdown(this)))
      if (typeof option == 'string') data[option].call($this)
    })
  }

  $.fn.dropdown.Constructor = Dropdown


  /* APPLY TO STANDARD DROPDOWN ELEMENTS
   * =================================== */

  $(function () {
    $('html').on('click.dropdown.data-api', clearMenus)
    $('body').on('click.dropdown.data-api', toggle, Dropdown.prototype.toggle)
  })

}( window.jQuery );/* =========================================================
 * bootstrap-modal.js v2.0.2
 * http://twitter.github.com/bootstrap/javascript.html#modals
 * =========================================================
 * Copyright 2012 Twitter, Inc.
 *
 * Licensed under the Apache License, Version 2.0 (the "License");
 * you may not use this file except in compliance with the License.
 * You may obtain a copy of the License at
 *
 * http://www.apache.org/licenses/LICENSE-2.0
 *
 * Unless required by applicable law or agreed to in writing, software
 * distributed under the License is distributed on an "AS IS" BASIS,
 * WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
 * See the License for the specific language governing permissions and
 * limitations under the License.
 * ========================================================= */


!function( $ ){

  "use strict"

 /* MODAL CLASS DEFINITION
  * ====================== */

  var Modal = function ( content, options ) {
    this.options = options
    this.$element = $(content)
      .delegate('[data-dismiss="modal"]', 'click.dismiss.modal', $.proxy(this.hide, this))
  }

  Modal.prototype = {

      constructor: Modal

    , toggle: function () {
        return this[!this.isShown ? 'show' : 'hide']()
      }

    , show: function () {
        var that = this

        if (this.isShown) return

        $('body').addClass('modal-open')

        this.isShown = true
        this.$element.trigger('show')

        escape.call(this)
        backdrop.call(this, function () {
          var transition = $.support.transition && that.$element.hasClass('fade')

          !that.$element.parent().length && that.$element.appendTo(document.body) //don't move modals dom position

          that.$element
            .show()

          if (transition) {
            that.$element[0].offsetWidth // force reflow
          }

          that.$element.addClass('in')

          transition ?
            that.$element.one($.support.transition.end, function () { that.$element.trigger('shown') }) :
            that.$element.trigger('shown')

        })
      }

    , hide: function ( e ) {
        e && e.preventDefault()

        if (!this.isShown) return

        var that = this
        this.isShown = false

        $('body').removeClass('modal-open')

        escape.call(this)

        this.$element
          .trigger('hide')
          .removeClass('in')

        $.support.transition && this.$element.hasClass('fade') ?
          hideWithTransition.call(this) :
          hideModal.call(this)
      }

  }


 /* MODAL PRIVATE METHODS
  * ===================== */

  function hideWithTransition() {
    var that = this
      , timeout = setTimeout(function () {
          that.$element.off($.support.transition.end)
          hideModal.call(that)
        }, 500)

    this.$element.one($.support.transition.end, function () {
      clearTimeout(timeout)
      hideModal.call(that)
    })
  }

  function hideModal( that ) {
    this.$element
      .hide()
      .trigger('hidden')

    backdrop.call(this)
  }

  function backdrop( callback ) {
    var that = this
      , animate = this.$element.hasClass('fade') ? 'fade' : ''

    if (this.isShown && this.options.backdrop) {
      var doAnimate = $.support.transition && animate

      this.$backdrop = $('<div class="modal-backdrop ' + animate + '" />')
        .appendTo(document.body)

      if (this.options.backdrop != 'static') {
        this.$backdrop.click($.proxy(this.hide, this))
      }

      if (doAnimate) this.$backdrop[0].offsetWidth // force reflow

      this.$backdrop.addClass('in')

      doAnimate ?
        this.$backdrop.one($.support.transition.end, callback) :
        callback()

    } else if (!this.isShown && this.$backdrop) {
      this.$backdrop.removeClass('in')

      $.support.transition && this.$element.hasClass('fade')?
        this.$backdrop.one($.support.transition.end, $.proxy(removeBackdrop, this)) :
        removeBackdrop.call(this)

    } else if (callback) {
      callback()
    }
  }

  function removeBackdrop() {
    this.$backdrop.remove()
    this.$backdrop = null
  }

  function escape() {
    var that = this
    if (this.isShown && this.options.keyboard) {
      $(document).on('keyup.dismiss.modal', function ( e ) {
        e.which == 27 && that.hide()
      })
    } else if (!this.isShown) {
      $(document).off('keyup.dismiss.modal')
    }
  }


 /* MODAL PLUGIN DEFINITION
  * ======================= */

  $.fn.modal = function ( option ) {
    return this.each(function () {
      var $this = $(this)
        , data = $this.data('modal')
        , options = $.extend({}, $.fn.modal.defaults, $this.data(), typeof option == 'object' && option)
      if (!data) $this.data('modal', (data = new Modal(this, options)))
      if (typeof option == 'string') data[option]()
      else if (options.show) data.show()
    })
  }

  $.fn.modal.defaults = {
      backdrop: true
    , keyboard: true
    , show: true
  }

  $.fn.modal.Constructor = Modal


 /* MODAL DATA-API
  * ============== */

  $(function () {
    $('body').on('click.modal.data-api', '[data-toggle="modal"]', function ( e ) {
      var $this = $(this), href
        , $target = $($this.attr('data-target') || (href = $this.attr('href')) && href.replace(/.*(?=#[^\s]+$)/, '')) //strip for ie7
        , option = $target.data('modal') ? 'toggle' : $.extend({}, $target.data(), $this.data())

      e.preventDefault()
      $target.modal(option)
    })
  })

}( window.jQuery );/* ===========================================================
 * bootstrap-tooltip.js v2.0.2
 * http://twitter.github.com/bootstrap/javascript.html#tooltips
 * Inspired by the original jQuery.tipsy by Jason Frame
 * ===========================================================
 * Copyright 2012 Twitter, Inc.
 *
 * Licensed under the Apache License, Version 2.0 (the "License");
 * you may not use this file except in compliance with the License.
 * You may obtain a copy of the License at
 *
 * http://www.apache.org/licenses/LICENSE-2.0
 *
 * Unless required by applicable law or agreed to in writing, software
 * distributed under the License is distributed on an "AS IS" BASIS,
 * WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
 * See the License for the specific language governing permissions and
 * limitations under the License.
 * ========================================================== */

!function( $ ) {

  "use strict"

 /* TOOLTIP PUBLIC CLASS DEFINITION
  * =============================== */

  var Tooltip = function ( element, options ) {
    this.init('tooltip', element, options)
  }

  Tooltip.prototype = {

    constructor: Tooltip

  , init: function ( type, element, options ) {
      var eventIn
        , eventOut

      this.type = type
      this.$element = $(element)
      this.options = this.getOptions(options)
      this.enabled = true

      if (this.options.trigger != 'manual') {
        eventIn  = this.options.trigger == 'hover' ? 'mouseenter' : 'focus'
        eventOut = this.options.trigger == 'hover' ? 'mouseleave' : 'blur'
        this.$element.on(eventIn, this.options.selector, $.proxy(this.enter, this))
        this.$element.on(eventOut, this.options.selector, $.proxy(this.leave, this))
      }

      this.options.selector ?
        (this._options = $.extend({}, this.options, { trigger: 'manual', selector: '' })) :
        this.fixTitle()
    }

  , getOptions: function ( options ) {
      options = $.extend({}, $.fn[this.type].defaults, options, this.$element.data())

      if (options.delay && typeof options.delay == 'number') {
        options.delay = {
          show: options.delay
        , hide: options.delay
        }
      }

      return options
    }

  , enter: function ( e ) {
      var self = $(e.currentTarget)[this.type](this._options).data(this.type)

      if (!self.options.delay || !self.options.delay.show) {
        self.show()
      } else {
        self.hoverState = 'in'
        setTimeout(function() {
          if (self.hoverState == 'in') {
            self.show()
          }
        }, self.options.delay.show)
      }
    }

  , leave: function ( e ) {
      var self = $(e.currentTarget)[this.type](this._options).data(this.type)

      if (!self.options.delay || !self.options.delay.hide) {
        self.hide()
      } else {
        self.hoverState = 'out'
        setTimeout(function() {
          if (self.hoverState == 'out') {
            self.hide()
          }
        }, self.options.delay.hide)
      }
    }

  , show: function () {
      var $tip
        , inside
        , pos
        , actualWidth
        , actualHeight
        , placement
        , tp

      if (this.hasContent() && this.enabled) {
        $tip = this.tip()
        this.setContent()

        if (this.options.animation) {
          $tip.addClass('fade')
        }

        placement = typeof this.options.placement == 'function' ?
          this.options.placement.call(this, $tip[0], this.$element[0]) :
          this.options.placement

        inside = /in/.test(placement)

        $tip
          .remove()
          .css({ top: 0, left: 0, display: 'block' })
          .appendTo(inside ? this.$element : document.body)

        pos = this.getPosition(inside)

        actualWidth = $tip[0].offsetWidth
        actualHeight = $tip[0].offsetHeight

        switch (inside ? placement.split(' ')[1] : placement) {
          case 'bottom':
            tp = {top: pos.top + pos.height, left: pos.left + pos.width / 2 - actualWidth / 2}
            break
          case 'top':
            tp = {top: pos.top - actualHeight, left: pos.left + pos.width / 2 - actualWidth / 2}
            break
          case 'left':
            tp = {top: pos.top + pos.height / 2 - actualHeight / 2, left: pos.left - actualWidth}
            break
          case 'right':
            tp = {top: pos.top + pos.height / 2 - actualHeight / 2, left: pos.left + pos.width}
            break
        }

        $tip
          .css(tp)
          .addClass(placement)
          .addClass('in')
      }
    }

  , setContent: function () {
      var $tip = this.tip()
      $tip.find('.tooltip-inner').html(this.getTitle())
      $tip.removeClass('fade in top bottom left right')
    }

  , hide: function () {
      var that = this
        , $tip = this.tip()

      $tip.removeClass('in')

      function removeWithAnimation() {
        var timeout = setTimeout(function () {
          $tip.off($.support.transition.end).remove()
        }, 500)

        $tip.one($.support.transition.end, function () {
          clearTimeout(timeout)
          $tip.remove()
        })
      }

      $.support.transition && this.$tip.hasClass('fade') ?
        removeWithAnimation() :
        $tip.remove()
    }

  , fixTitle: function () {
      var $e = this.$element
      if ($e.attr('title') || typeof($e.attr('data-original-title')) != 'string') {
        $e.attr('data-original-title', $e.attr('title') || '').removeAttr('title')
      }
    }

  , hasContent: function () {
      return this.getTitle()
    }

  , getPosition: function (inside) {
      return $.extend({}, (inside ? {top: 0, left: 0} : this.$element.offset()), {
        width: this.$element[0].offsetWidth
      , height: this.$element[0].offsetHeight
      })
    }

  , getTitle: function () {
      var title
        , $e = this.$element
        , o = this.options

      title = $e.attr('data-original-title')
        || (typeof o.title == 'function' ? o.title.call($e[0]) :  o.title)

      title = (title || '').toString().replace(/(^\s*|\s*$)/, "")

      return title
    }

  , tip: function () {
      return this.$tip = this.$tip || $(this.options.template)
    }

  , validate: function () {
      if (!this.$element[0].parentNode) {
        this.hide()
        this.$element = null
        this.options = null
      }
    }

  , enable: function () {
      this.enabled = true
    }

  , disable: function () {
      this.enabled = false
    }

  , toggleEnabled: function () {
      this.enabled = !this.enabled
    }

  , toggle: function () {
      this[this.tip().hasClass('in') ? 'hide' : 'show']()
    }

  }


 /* TOOLTIP PLUGIN DEFINITION
  * ========================= */

  $.fn.tooltip = function ( option ) {
    return this.each(function () {
      var $this = $(this)
        , data = $this.data('tooltip')
        , options = typeof option == 'object' && option
      if (!data) $this.data('tooltip', (data = new Tooltip(this, options)))
      if (typeof option == 'string') data[option]()
    })
  }

  $.fn.tooltip.Constructor = Tooltip

  $.fn.tooltip.defaults = {
    animation: true
  , delay: 0
  , selector: false
  , placement: 'top'
  , trigger: 'hover'
  , title: ''
  , template: '<div class="tooltip"><div class="tooltip-arrow"></div><div class="tooltip-inner"></div></div>'
  }

}( window.jQuery );/* ===========================================================
 * bootstrap-popover.js v2.0.2
 * http://twitter.github.com/bootstrap/javascript.html#popovers
 * ===========================================================
 * Copyright 2012 Twitter, Inc.
 *
 * Licensed under the Apache License, Version 2.0 (the "License");
 * you may not use this file except in compliance with the License.
 * You may obtain a copy of the License at
 *
 * http://www.apache.org/licenses/LICENSE-2.0
 *
 * Unless required by applicable law or agreed to in writing, software
 * distributed under the License is distributed on an "AS IS" BASIS,
 * WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
 * See the License for the specific language governing permissions and
 * limitations under the License.
 * =========================================================== */


!function( $ ) {

 "use strict"

  var Popover = function ( element, options ) {
    this.init('popover', element, options)
  }

  /* NOTE: POPOVER EXTENDS BOOTSTRAP-TOOLTIP.js
     ========================================== */

  Popover.prototype = $.extend({}, $.fn.tooltip.Constructor.prototype, {

    constructor: Popover

  , setContent: function () {
      var $tip = this.tip()
        , title = this.getTitle()
        , content = this.getContent()

      $tip.find('.popover-title')[ $.type(title) == 'object' ? 'append' : 'html' ](title)
      $tip.find('.popover-content > *')[ $.type(content) == 'object' ? 'append' : 'html' ](content)

      $tip.removeClass('fade top bottom left right in')
    }

  , hasContent: function () {
      return this.getTitle() || this.getContent()
    }

  , getContent: function () {
      var content
        , $e = this.$element
        , o = this.options

      content = $e.attr('data-content')
        || (typeof o.content == 'function' ? o.content.call($e[0]) :  o.content)

      content = content.toString().replace(/(^\s*|\s*$)/, "")

      return content
    }

  , tip: function() {
      if (!this.$tip) {
        this.$tip = $(this.options.template)
      }
      return this.$tip
    }

  })


 /* POPOVER PLUGIN DEFINITION
  * ======================= */

  $.fn.popover = function ( option ) {
    return this.each(function () {
      var $this = $(this)
        , data = $this.data('popover')
        , options = typeof option == 'object' && option
      if (!data) $this.data('popover', (data = new Popover(this, options)))
      if (typeof option == 'string') data[option]()
    })
  }

  $.fn.popover.Constructor = Popover

  $.fn.popover.defaults = $.extend({} , $.fn.tooltip.defaults, {
    placement: 'right'
  , content: ''
  , template: '<div class="popover"><div class="arrow"></div><div class="popover-inner"><h3 class="popover-title"></h3><div class="popover-content"><p></p></div></div></div>'
  })

}( window.jQuery );/* =============================================================
 * bootstrap-scrollspy.js v2.0.2
 * http://twitter.github.com/bootstrap/javascript.html#scrollspy
 * =============================================================
 * Copyright 2012 Twitter, Inc.
 *
 * Licensed under the Apache License, Version 2.0 (the "License");
 * you may not use this file except in compliance with the License.
 * You may obtain a copy of the License at
 *
 * http://www.apache.org/licenses/LICENSE-2.0
 *
 * Unless required by applicable law or agreed to in writing, software
 * distributed under the License is distributed on an "AS IS" BASIS,
 * WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
 * See the License for the specific language governing permissions and
 * limitations under the License.
 * ============================================================== */

!function ( $ ) {

  "use strict"

  /* SCROLLSPY CLASS DEFINITION
   * ========================== */

  function ScrollSpy( element, options) {
    var process = $.proxy(this.process, this)
      , $element = $(element).is('body') ? $(window) : $(element)
      , href
    this.options = $.extend({}, $.fn.scrollspy.defaults, options)
    this.$scrollElement = $element.on('scroll.scroll.data-api', process)
    this.selector = (this.options.target
      || ((href = $(element).attr('href')) && href.replace(/.*(?=#[^\s]+$)/, '')) //strip for ie7
      || '') + ' .nav li > a'
    this.$body = $('body').on('click.scroll.data-api', this.selector, process)
    this.refresh()
    this.process()
  }

  ScrollSpy.prototype = {

      constructor: ScrollSpy

    , refresh: function () {
        this.targets = this.$body
          .find(this.selector)
          .map(function () {
            var href = $(this).attr('href')
            return /^#\w/.test(href) && $(href).length ? href : null
          })

        this.offsets = $.map(this.targets, function (id) {
          return $(id).position().top
        })
      }

    , process: function () {
        var scrollTop = this.$scrollElement.scrollTop() + this.options.offset
          , offsets = this.offsets
          , targets = this.targets
          , activeTarget = this.activeTarget
          , i

        for (i = offsets.length; i--;) {
          activeTarget != targets[i]
            && scrollTop >= offsets[i]
            && (!offsets[i + 1] || scrollTop <= offsets[i + 1])
            && this.activate( targets[i] )
        }
      }

    , activate: function (target) {
        var active

        this.activeTarget = target

        this.$body
          .find(this.selector).parent('.active')
          .removeClass('active')

        active = this.$body
          .find(this.selector + '[href="' + target + '"]')
          .parent('li')
          .addClass('active')

        if ( active.parent('.dropdown-menu') )  {
          active.closest('li.dropdown').addClass('active')
        }
      }

  }


 /* SCROLLSPY PLUGIN DEFINITION
  * =========================== */

  $.fn.scrollspy = function ( option ) {
    return this.each(function () {
      var $this = $(this)
        , data = $this.data('scrollspy')
        , options = typeof option == 'object' && option
      if (!data) $this.data('scrollspy', (data = new ScrollSpy(this, options)))
      if (typeof option == 'string') data[option]()
    })
  }

  $.fn.scrollspy.Constructor = ScrollSpy

  $.fn.scrollspy.defaults = {
    offset: 10
  }


 /* SCROLLSPY DATA-API
  * ================== */

  $(function () {
    $('[data-spy="scroll"]').each(function () {
      var $spy = $(this)
      $spy.scrollspy($spy.data())
    })
  })

}( window.jQuery );/* ========================================================
 * bootstrap-tab.js v2.0.2
 * http://twitter.github.com/bootstrap/javascript.html#tabs
 * ========================================================
 * Copyright 2012 Twitter, Inc.
 *
 * Licensed under the Apache License, Version 2.0 (the "License");
 * you may not use this file except in compliance with the License.
 * You may obtain a copy of the License at
 *
 * http://www.apache.org/licenses/LICENSE-2.0
 *
 * Unless required by applicable law or agreed to in writing, software
 * distributed under the License is distributed on an "AS IS" BASIS,
 * WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
 * See the License for the specific language governing permissions and
 * limitations under the License.
 * ======================================================== */


!function( $ ){

  "use strict"

 /* TAB CLASS DEFINITION
  * ==================== */

  var Tab = function ( element ) {
    this.element = $(element)
  }

  Tab.prototype = {

    constructor: Tab

  , show: function () {
      var $this = this.element
        , $ul = $this.closest('ul:not(.dropdown-menu)')
        , selector = $this.attr('data-target')
        , previous
        , $target

      if (!selector) {
        selector = $this.attr('href')
        selector = selector && selector.replace(/.*(?=#[^\s]*$)/, '') //strip for ie7
      }

      if ( $this.parent('li').hasClass('active') ) return

      previous = $ul.find('.active a').last()[0]

      $this.trigger({
        type: 'show'
      , relatedTarget: previous
      })

      $target = $(selector)

      this.activate($this.parent('li'), $ul)
      this.activate($target, $target.parent(), function () {
        $this.trigger({
          type: 'shown'
        , relatedTarget: previous
        })
      })
    }

  , activate: function ( element, container, callback) {
      var $active = container.find('> .active')
        , transition = callback
            && $.support.transition
            && $active.hasClass('fade')

      function next() {
        $active
          .removeClass('active')
          .find('> .dropdown-menu > .active')
          .removeClass('active')

        element.addClass('active')

        if (transition) {
          element[0].offsetWidth // reflow for transition
          element.addClass('in')
        } else {
          element.removeClass('fade')
        }

        if ( element.parent('.dropdown-menu') ) {
          element.closest('li.dropdown').addClass('active')
        }

        callback && callback()
      }

      transition ?
        $active.one($.support.transition.end, next) :
        next()

      $active.removeClass('in')
    }
  }


 /* TAB PLUGIN DEFINITION
  * ===================== */

  $.fn.tab = function ( option ) {
    return this.each(function () {
      var $this = $(this)
        , data = $this.data('tab')
      if (!data) $this.data('tab', (data = new Tab(this)))
      if (typeof option == 'string') data[option]()
    })
  }

  $.fn.tab.Constructor = Tab


 /* TAB DATA-API
  * ============ */

  $(function () {
    $('body').on('click.tab.data-api', '[data-toggle="tab"], [data-toggle="pill"]', function (e) {
      e.preventDefault()
      $(this).tab('show')
    })
  })

}( window.jQuery );/* =============================================================
 * bootstrap-typeahead.js v2.0.2
 * http://twitter.github.com/bootstrap/javascript.html#typeahead
 * =============================================================
 * Copyright 2012 Twitter, Inc.
 *
 * Licensed under the Apache License, Version 2.0 (the "License");
 * you may not use this file except in compliance with the License.
 * You may obtain a copy of the License at
 *
 * http://www.apache.org/licenses/LICENSE-2.0
 *
 * Unless required by applicable law or agreed to in writing, software
 * distributed under the License is distributed on an "AS IS" BASIS,
 * WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
 * See the License for the specific language governing permissions and
 * limitations under the License.
 * ============================================================ */

!function( $ ){

  "use strict"

  var Typeahead = function ( element, options ) {
    this.$element = $(element)
    this.options = $.extend({}, $.fn.typeahead.defaults, options)
    this.matcher = this.options.matcher || this.matcher
    this.sorter = this.options.sorter || this.sorter
    this.highlighter = this.options.highlighter || this.highlighter
    this.$menu = $(this.options.menu).appendTo('body')
    this.source = this.options.source
    this.shown = false
    this.listen()
  }

  Typeahead.prototype = {

    constructor: Typeahead

  , select: function () {
      var val = this.$menu.find('.active').attr('data-value')
      this.$element.val(val)
      this.$element.change();
      return this.hide()
    }

  , show: function () {
      var pos = $.extend({}, this.$element.offset(), {
        height: this.$element[0].offsetHeight
      })

      this.$menu.css({
        top: pos.top + pos.height
      , left: pos.left
      })

      this.$menu.show()
      this.shown = true
      return this
    }

  , hide: function () {
      this.$menu.hide()
      this.shown = false
      return this
    }

  , lookup: function (event) {
      var that = this
        , items
        , q

      this.query = this.$element.val()

      if (!this.query) {
        return this.shown ? this.hide() : this
      }

      items = $.grep(this.source, function (item) {
        if (that.matcher(item)) return item
      })

      items = this.sorter(items)

      if (!items.length) {
        return this.shown ? this.hide() : this
      }

      return this.render(items.slice(0, this.options.items)).show()
    }

  , matcher: function (item) {
      return ~item.toLowerCase().indexOf(this.query.toLowerCase())
    }

  , sorter: function (items) {
      var beginswith = []
        , caseSensitive = []
        , caseInsensitive = []
        , item

      while (item = items.shift()) {
        if (!item.toLowerCase().indexOf(this.query.toLowerCase())) beginswith.push(item)
        else if (~item.indexOf(this.query)) caseSensitive.push(item)
        else caseInsensitive.push(item)
      }

      return beginswith.concat(caseSensitive, caseInsensitive)
    }

  , highlighter: function (item) {
      return item.replace(new RegExp('(' + this.query + ')', 'ig'), function ($1, match) {
        return '<strong>' + match + '</strong>'
      })
    }

  , render: function (items) {
      var that = this

      items = $(items).map(function (i, item) {
        i = $(that.options.item).attr('data-value', item)
        i.find('a').html(that.highlighter(item))
        return i[0]
      })

      items.first().addClass('active')
      this.$menu.html(items)
      return this
    }

  , next: function (event) {
      var active = this.$menu.find('.active').removeClass('active')
        , next = active.next()

      if (!next.length) {
        next = $(this.$menu.find('li')[0])
      }

      next.addClass('active')
    }

  , prev: function (event) {
      var active = this.$menu.find('.active').removeClass('active')
        , prev = active.prev()

      if (!prev.length) {
        prev = this.$menu.find('li').last()
      }

      prev.addClass('active')
    }

  , listen: function () {
      this.$element
        .on('blur',     $.proxy(this.blur, this))
        .on('keypress', $.proxy(this.keypress, this))
        .on('keyup',    $.proxy(this.keyup, this))

      if ($.browser.webkit || $.browser.msie) {
        this.$element.on('keydown', $.proxy(this.keypress, this))
      }

      this.$menu
        .on('click', $.proxy(this.click, this))
        .on('mouseenter', 'li', $.proxy(this.mouseenter, this))
    }

  , keyup: function (e) {
      switch(e.keyCode) {
        case 40: // down arrow
        case 38: // up arrow
          break

        case 9: // tab
        case 13: // enter
          if (!this.shown) return
          this.select()
          break

        case 27: // escape
          if (!this.shown) return
          this.hide()
          break

        default:
          this.lookup()
      }

      e.stopPropagation()
      e.preventDefault()
  }

  , keypress: function (e) {
      if (!this.shown) return

      switch(e.keyCode) {
        case 9: // tab
        case 13: // enter
        case 27: // escape
          e.preventDefault()
          break

        case 38: // up arrow
          e.preventDefault()
          this.prev()
          break

        case 40: // down arrow
          e.preventDefault()
          this.next()
          break
      }

      e.stopPropagation()
    }

  , blur: function (e) {
      var that = this
      setTimeout(function () { that.hide() }, 150)
    }

  , click: function (e) {
      e.stopPropagation()
      e.preventDefault()
      this.select()
    }

  , mouseenter: function (e) {
      this.$menu.find('.active').removeClass('active')
      $(e.currentTarget).addClass('active')
    }

  }


  /* TYPEAHEAD PLUGIN DEFINITION
   * =========================== */

  $.fn.typeahead = function ( option ) {
    return this.each(function () {
      var $this = $(this)
        , data = $this.data('typeahead')
        , options = typeof option == 'object' && option
      if (!data) $this.data('typeahead', (data = new Typeahead(this, options)))
      if (typeof option == 'string') data[option]()
    })
  }

  $.fn.typeahead.defaults = {
    source: []
  , items: 8
  , menu: '<ul class="typeahead dropdown-menu"></ul>'
  , item: '<li><a href="#"></a></li>'
  }

  $.fn.typeahead.Constructor = Typeahead


 /* TYPEAHEAD DATA-API
  * ================== */

  $(function () {
    $('body').on('focus.typeahead.data-api', '[data-provide="typeahead"]', function (e) {
      var $this = $(this)
      if ($this.data('typeahead')) return
      e.preventDefault()
      $this.typeahead($this.data())
    })
  })

}( window.jQuery );
var countries = [{'code': 'AD', 'name': 'Andorra'}, {'code': 'AE', 'name': 'United Arab Emirates'}, {'code': 'AF', 'name': 'Afghanistan'}, {'code': 'AG', 'name': 'Antigua and Barbuda'}, {'code': 'AI', 'name': 'Anguilla'}, {'code': 'AL', 'name': 'Albania'}, {'code': 'AM', 'name': 'Armenia'}, {'code': 'AN', 'name': 'Netherlands Antilles'}, {'code': 'AO', 'name': 'Angola'}, {'code': 'AQ', 'name': 'Antarctica'}, {'code': 'AR', 'name': 'Argentina'}, {'code': 'AS', 'name': 'American Samoa'}, {'code': 'AT', 'name': 'Austria'}, {'code': 'AU', 'name': 'Australia'}, {'code': 'AW', 'name': 'Aruba'}, {'code': 'AX', 'name': 'Aland Islands'}, {'code': 'AZ', 'name': 'Azerbaijan'}, {'code': 'BA', 'name': 'Bosnia and Herzegovina'}, {'code': 'BB', 'name': 'Barbados'}, {'code': 'BD', 'name': 'Bangladesh'}, {'code': 'BE', 'name': 'Belgium'}, {'code': 'BF', 'name': 'Burkina Faso'}, {'code': 'BG', 'name': 'Bulgaria'}, {'code': 'BH', 'name': 'Bahrain'}, {'code': 'BI', 'name': 'Burundi'}, {'code': 'BJ', 'name': 'Benin'}, {'code': 'BM', 'name': 'Bermuda'}, {'code': 'BN', 'name': 'Brunei Darussalam'}, {'code': 'BO', 'name': 'Bolivia'}, {'code': 'BR', 'name': 'Brazil'}, {'code': 'BS', 'name': 'Bahamas'}, {'code': 'BT', 'name': 'Bhutan'}, {'code': 'BV', 'name': 'Bouvet Island'}, {'code': 'BW', 'name': 'Botswana'}, {'code': 'BY', 'name': 'Belarus'}, {'code': 'BZ', 'name': 'Belize'}, {'code': 'CA', 'name': 'Canada'}, {'code': 'CC', 'name': 'Cocos (Keeling) Islands'}, {'code': 'CD', 'name': 'Democratic Republic of the Congo'}, {'code': 'CF', 'name': 'Central African Republic'}, {'code': 'CG', 'name': 'Congo'}, {'code': 'CH', 'name': 'Switzerland'}, {'code': 'CI', 'name': "Cote D'Ivoire (Ivory Coast)"}, {'code': 'CK', 'name': 'Cook Islands'}, {'code': 'CL', 'name': 'Chile'}, {'code': 'CM', 'name': 'Cameroon'}, {'code': 'CN', 'name': 'China'}, {'code': 'CO', 'name': 'Colombia'}, {'code': 'CR', 'name': 'Costa Rica'}, {'code': 'CS', 'name': 'Serbia and Montenegro'}, {'code': 'CU', 'name': 'Cuba'}, {'code': 'CV', 'name': 'Cape Verde'}, {'code': 'CX', 'name': 'Christmas Island'}, {'code': 'CY', 'name': 'Cyprus'}, {'code': 'CZ', 'name': 'Czech Republic'}, {'code': 'DE', 'name': 'Germany'}, {'code': 'DJ', 'name': 'Djibouti'}, {'code': 'DK', 'name': 'Denmark'}, {'code': 'DM', 'name': 'Dominica'}, {'code': 'DO', 'name': 'Dominican Republic'}, {'code': 'DZ', 'name': 'Algeria'}, {'code': 'EC', 'name': 'Ecuador'}, {'code': 'EE', 'name': 'Estonia'}, {'code': 'EG', 'name': 'Egypt'}, {'code': 'EH', 'name': 'Western Sahara'}, {'code': 'ER', 'name': 'Eritrea'}, {'code': 'ES', 'name': 'Spain'}, {'code': 'ET', 'name': 'Ethiopia'}, {'code': 'FI', 'name': 'Finland'}, {'code': 'FJ', 'name': 'Fiji'}, {'code': 'FK', 'name': 'Falkland Islands (Malvinas)'}, {'code': 'FM', 'name': 'Federated States of Micronesia'}, {'code': 'FO', 'name': 'Faroe Islands'}, {'code': 'FR', 'name': 'France'}, {'code': 'GA', 'name': 'Gabon'}, {'code': 'GB', 'name': 'Great Britain (UK)'}, {'code': 'GD', 'name': 'Grenada'}, {'code': 'GE', 'name': 'Georgia'}, {'code': 'GF', 'name': 'French Guiana'}, {'code': 'GH', 'name': 'Ghana'}, {'code': 'GI', 'name': 'Gibraltar'}, {'code': 'GL', 'name': 'Greenland'}, {'code': 'GM', 'name': 'Gambia'}, {'code': 'GN', 'name': 'Guinea'}, {'code': 'GP', 'name': 'Guadeloupe'}, {'code': 'GQ', 'name': 'Equatorial Guinea'}, {'code': 'GR', 'name': 'Greece'}, {'code': 'GS', 'name': 'S. Georgia and S. Sandwich Islands'}, {'code': 'GT', 'name': 'Guatemala'}, {'code': 'GU', 'name': 'Guam'}, {'code': 'GW', 'name': 'Guinea-Bissau'}, {'code': 'GY', 'name': 'Guyana'}, {'code': 'HK', 'name': 'Hong Kong'}, {'code': 'HM', 'name': 'Heard Island and McDonald Islands'}, {'code': 'HN', 'name': 'Honduras'}, {'code': 'HR', 'name': 'Croatia (Hrvatska)'}, {'code': 'HT', 'name': 'Haiti'}, {'code': 'HU', 'name': 'Hungary'}, {'code': 'ID', 'name': 'Indonesia'}, {'code': 'IE', 'name': 'Ireland'}, {'code': 'IL', 'name': 'Israel'}, {'code': 'IN', 'name': 'India'}, {'code': 'IO', 'name': 'British Indian Ocean Territory'}, {'code': 'IQ', 'name': 'Iraq'}, {'code': 'IR', 'name': 'Iran'}, {'code': 'IS', 'name': 'Iceland'}, {'code': 'IT', 'name': 'Italy'}, {'code': 'JM', 'name': 'Jamaica'}, {'code': 'JO', 'name': 'Jordan'}, {'code': 'JP', 'name': 'Japan'}, {'code': 'KE', 'name': 'Kenya'}, {'code': 'KG', 'name': 'Kyrgyzstan'}, {'code': 'KH', 'name': 'Cambodia'}, {'code': 'KI', 'name': 'Kiribati'}, {'code': 'KM', 'name': 'Comoros'}, {'code': 'KN', 'name': 'Saint Kitts and Nevis'}, {'code': 'KP', 'name': 'Korea (North)'}, {'code': 'KR', 'name': 'Korea (South)'}, {'code': 'KW', 'name': 'Kuwait'}, {'code': 'KY', 'name': 'Cayman Islands'}, {'code': 'KZ', 'name': 'Kazakhstan'}, {'code': 'LA', 'name': 'Laos'}, {'code': 'LB', 'name': 'Lebanon'}, {'code': 'LC', 'name': 'Saint Lucia'}, {'code': 'LI', 'name': 'Liechtenstein'}, {'code': 'LK', 'name': 'Sri Lanka'}, {'code': 'LR', 'name': 'Liberia'}, {'code': 'LS', 'name': 'Lesotho'}, {'code': 'LT', 'name': 'Lithuania'}, {'code': 'LU', 'name': 'Luxembourg'}, {'code': 'LV', 'name': 'Latvia'}, {'code': 'LY', 'name': 'Libya'}, {'code': 'MA', 'name': 'Morocco'}, {'code': 'MC', 'name': 'Monaco'}, {'code': 'MD', 'name': 'Moldova'}, {'code': 'MG', 'name': 'Madagascar'}, {'code': 'MH', 'name': 'Marshall Islands'}, {'code': 'MK', 'name': 'Macedonia'}, {'code': 'ML', 'name': 'Mali'}, {'code': 'MM', 'name': 'Myanmar'}, {'code': 'MN', 'name': 'Mongolia'}, {'code': 'MO', 'name': 'Macao'}, {'code': 'MP', 'name': 'Northern Mariana Islands'}, {'code': 'MQ', 'name': 'Martinique'}, {'code': 'MR', 'name': 'Mauritania'}, {'code': 'MS', 'name': 'Montserrat'}, {'code': 'MT', 'name': 'Malta'}, {'code': 'MU', 'name': 'Mauritius'}, {'code': 'MV', 'name': 'Maldives'}, {'code': 'MW', 'name': 'Malawi'}, {'code': 'MX', 'name': 'Mexico'}, {'code': 'MY', 'name': 'Malaysia'}, {'code': 'MZ', 'name': 'Mozambique'}, {'code': 'NA', 'name': 'Namibia'}, {'code': 'NC', 'name': 'New Caledonia'}, {'code': 'NE', 'name': 'Niger'}, {'code': 'NF', 'name': 'Norfolk Island'}, {'code': 'NG', 'name': 'Nigeria'}, {'code': 'NI', 'name': 'Nicaragua'}, {'code': 'NL', 'name': 'Netherlands'}, {'code': 'NO', 'name': 'Norway'}, {'code': 'NP', 'name': 'Nepal'}, {'code': 'NR', 'name': 'Nauru'}, {'code': 'NU', 'name': 'Niue'}, {'code': 'NZ', 'name': 'New Zealand (Aotearoa)'}, {'code': 'OM', 'name': 'Oman'}, {'code': 'PA', 'name': 'Panama'}, {'code': 'PE', 'name': 'Peru'}, {'code': 'PF', 'name': 'French Polynesia'}, {'code': 'PG', 'name': 'Papua New Guinea'}, {'code': 'PH', 'name': 'Philippines'}, {'code': 'PK', 'name': 'Pakistan'}, {'code': 'PL', 'name': 'Poland'}, {'code': 'PM', 'name': 'Saint Pierre and Miquelon'}, {'code': 'PN', 'name': 'Pitcairn'}, {'code': 'PR', 'name': 'Puerto Rico'}, {'code': 'PS', 'name': 'Palestinian Territory'}, {'code': 'PT', 'name': 'Portugal'}, {'code': 'PW', 'name': 'Palau'}, {'code': 'PY', 'name': 'Paraguay'}, {'code': 'QA', 'name': 'Qatar'}, {'code': 'RE', 'name': 'Reunion'}, {'code': 'RO', 'name': 'Romania'}, {'code': 'RU', 'name': 'Russian Federation'}, {'code': 'RW', 'name': 'Rwanda'}, {'code': 'SA', 'name': 'Saudi Arabia'}, {'code': 'SB', 'name': 'Solomon Islands'}, {'code': 'SC', 'name': 'Seychelles'}, {'code': 'SD', 'name': 'Sudan'}, {'code': 'SE', 'name': 'Sweden'}, {'code': 'SG', 'name': 'Singapore'}, {'code': 'SH', 'name': 'Saint Helena'}, {'code': 'SI', 'name': 'Slovenia'}, {'code': 'SJ', 'name': 'Svalbard and Jan Mayen'}, {'code': 'SK', 'name': 'Slovakia'}, {'code': 'SL', 'name': 'Sierra Leone'}, {'code': 'SM', 'name': 'San Marino'}, {'code': 'SN', 'name': 'Senegal'}, {'code': 'SO', 'name': 'Somalia'}, {'code': 'SR', 'name': 'Suriname'}, {'code': 'ST', 'name': 'Sao Tome and Principe'}, {'code': 'SV', 'name': 'El Salvador'}, {'code': 'SY', 'name': 'Syria'}, {'code': 'SZ', 'name': 'Swaziland'}, {'code': 'TC', 'name': 'Turks and Caicos Islands'}, {'code': 'TD', 'name': 'Chad'}, {'code': 'TF', 'name': 'French Southern Territories'}, {'code': 'TG', 'name': 'Togo'}, {'code': 'TH', 'name': 'Thailand'}, {'code': 'TJ', 'name': 'Tajikistan'}, {'code': 'TK', 'name': 'Tokelau'}, {'code': 'TL', 'name': 'Timor-Leste'}, {'code': 'TM', 'name': 'Turkmenistan'}, {'code': 'TN', 'name': 'Tunisia'}, {'code': 'TO', 'name': 'Tonga'}, {'code': 'TP', 'name': 'East Timor'}, {'code': 'TR', 'name': 'Turkey'}, {'code': 'TT', 'name': 'Trinidad and Tobago'}, {'code': 'TV', 'name': 'Tuvalu'}, {'code': 'TW', 'name': 'Taiwan'}, {'code': 'TZ', 'name': 'Tanzania'}, {'code': 'UA', 'name': 'Ukraine'}, {'code': 'UG', 'name': 'Uganda'}, {'code': 'UK', 'name': 'United Kingdom'}, {'code': 'UM', 'name': 'United States Minor Outlying Islands'}, {'code': 'US', 'name': 'United States'}, {'code': 'UY', 'name': 'Uruguay'}, {'code': 'UZ', 'name': 'Uzbekistan'}, {'code': 'VA', 'name': 'Vatican City State (Holy See)'}, {'code': 'VC', 'name': 'Saint Vincent and the Grenadines'}, {'code': 'VE', 'name': 'Venezuela'}, {'code': 'VG', 'name': 'Virgin Islands (British)'}, {'code': 'VI', 'name': 'Virgin Islands (U.S.)'}, {'code': 'VN', 'name': 'Viet Nam'}, {'code': 'VU', 'name': 'Vanuatu'}, {'code': 'WF', 'name': 'Wallis and Futuna'}, {'code': 'WS', 'name': 'Samoa'}, {'code': 'YE', 'name': 'Yemen'}, {'code': 'YT', 'name': 'Mayotte'}, {'code': 'YU', 'name': 'Yugoslavia (former)'}, {'code': 'ZA', 'name': 'South Africa'}, {'code': 'ZM', 'name': 'Zambia'}, {'code': 'ZR', 'name': 'Zaire (former)'}, {'code': 'ZW', 'name': 'Zimbabwe'}];

(function(){function e(a,b){try{for(var c in b)Object.defineProperty(a.prototype,c,{value:b[c],enumerable:!1})}catch(d){a.prototype=b}}function g(a){var b=-1,c=a.length,d=[];while(++b<c)d.push(a[b]);return d}function h(a){return Array.prototype.slice.call(a)}function k(){}function n(){return this}function o(a,b,c){return function(){var d=c.apply(b,arguments);return arguments.length?a:d}}function p(a){return a!=null&&!isNaN(a)}function q(a){return a.length}function s(a){return a==null}function t(a){return a.replace(/(^\s+)|(\s+$)/g,"").replace(/\s+/g," ")}function u(a){var b=1;while(a*b%1)b*=10;return b}function x(){}function y(a){function d(){var c=b,d=-1,e=c.length,f;while(++d<e)(f=c[d].on)&&f.apply(this,arguments);return a}var b=[],c=new k;return d.on=function(d,e){var f=c.get(d),g;return arguments.length<2?f&&f.on:(f&&(f.on=null,b=b.slice(0,g=b.indexOf(f)).concat(b.slice(g+1)),c.remove(d)),e&&b.push(c.set(d,{on:e})),a)},d}function B(a,b){return b-(a?1+Math.floor(Math.log(a+Math.pow(10,1+Math.floor(Math.log(a)/Math.LN10)-b))/Math.LN10):1)}function C(a){return a+""}function D(a){var b=a.lastIndexOf("."),c=b>=0?a.substring(b):(b=a.length,""),d=[];while(b>0)d.push(a.substring(b-=3,b+3));return d.reverse().join(",")+c}function F(a,b){return{scale:Math.pow(10,(8-b)*3),symbol:a}}function L(a){return function(b){return b<=0?0:b>=1?1:a(b)}}function M(a){return function(b){return 1-a(1-b)}}function N(a){return function(b){return.5*(b<.5?a(2*b):2-a(2-2*b))}}function O(a){return a}function P(a){return function(b){return Math.pow(b,a)}}function Q(a){return 1-Math.cos(a*Math.PI/2)}function R(a){return Math.pow(2,10*(a-1))}function S(a){return 1-Math.sqrt(1-a*a)}function T(a,b){var c;return arguments.length<2&&(b=.45),arguments.length<1?(a=1,c=b/4):c=b/(2*Math.PI)*Math.asin(1/a),function(d){return 1+a*Math.pow(2,10*-d)*Math.sin((d-c)*2*Math.PI/b)}}function U(a){return a||(a=1.70158),function(b){return b*b*((a+1)*b-a)}}function V(a){return a<1/2.75?7.5625*a*a:a<2/2.75?7.5625*(a-=1.5/2.75)*a+.75:a<2.5/2.75?7.5625*(a-=2.25/2.75)*a+.9375:7.5625*(a-=2.625/2.75)*a+.984375}function W(){d3.event.stopPropagation(),d3.event.preventDefault()}function X(){var a=d3.event,b;while(b=a.sourceEvent)a=b;return a}function Y(a){var b=new x,c=0,d=arguments.length;while(++c<d)b[arguments[c]]=y(b);return b.of=function(c,d){return function(e){try{var f=e.sourceEvent=d3.event;e.target=a,d3.event=e,b[e.type].apply(c,d)}finally{d3.event=f}}},b}function $(a){return a=="transform"?d3.interpolateTransform:d3.interpolate}function _(a,b){return b=b-(a=+a)?1/(b-a):0,function(c){return(c-a)*b}}function ba(a,b){return b=b-(a=+a)?1/(b-a):0,function(c){return Math.max(0,Math.min(1,(c-a)*b))}}function bb(a,b,c){return new bc(a,b,c)}function bc(a,b,c){this.r=a,this.g=b,this.b=c}function bd(a){return a<16?"0"+Math.max(0,a).toString(16):Math.min(255,a).toString(16)}function be(a,b,c){var d=0,e=0,f=0,g,h,i;g=/([a-z]+)\((.*)\)/i.exec(a);if(g){h=g[2].split(",");switch(g[1]){case"hsl":return c(parseFloat(h[0]),parseFloat(h[1])/100,parseFloat(h[2])/100);case"rgb":return b(bg(h[0]),bg(h[1]),bg(h[2]))}}return(i=bh.get(a))?b(i.r,i.g,i.b):(a!=null&&a.charAt(0)==="#"&&(a.length===4?(d=a.charAt(1),d+=d,e=a.charAt(2),e+=e,f=a.charAt(3),f+=f):a.length===7&&(d=a.substring(1,3),e=a.substring(3,5),f=a.substring(5,7)),d=parseInt(d,16),e=parseInt(e,16),f=parseInt(f,16)),b(d,e,f))}function bf(a,b,c){var d=Math.min(a/=255,b/=255,c/=255),e=Math.max(a,b,c),f=e-d,g,h,i=(e+d)/2;return f?(h=i<.5?f/(e+d):f/(2-e-d),a==e?g=(b-c)/f+(b<c?6:0):b==e?g=(c-a)/f+2:g=(a-b)/f+4,g*=60):h=g=0,bi(g,h,i)}function bg(a){var b=parseFloat(a);return a.charAt(a.length-1)==="%"?Math.round(b*2.55):b}function bi(a,b,c){return new bj(a,b,c)}function bj(a,b,c){this.h=a,this.s=b,this.l=c}function bk(a,b,c){function f(a){return a>360?a-=360:a<0&&(a+=360),a<60?d+(e-d)*a/60:a<180?e:a<240?d+(e-d)*(240-a)/60:d}function g(a){return Math.round(f(a)*255)}var d,e;return a%=360,a<0&&(a+=360),b=b<0?0:b>1?1:b,c=c<0?0:c>1?1:c,e=c<=.5?c*(1+b):c+b-c*b,d=2*c-e,bb(g(a+120),g(a),g(a-120))}function bl(a){return j(a,br),a}function bs(a){return function(){return bm(a,this)}}function bt(a){return function(){return bn(a,this)}}function bv(a,b){function f(){if(b=this.classList)return b.add(a);var b=this.className,d=b.baseVal!=null,e=d?b.baseVal:b;c.lastIndex=0,c.test(e)||(e=t(e+" "+a),d?b.baseVal=e:this.className=e)}function g(){if(b=this.classList)return b.remove(a);var b=this.className,d=b.baseVal!=null,e=d?b.baseVal:b;e=t(e.replace(c," ")),d?b.baseVal=e:this.className=e}function h(){(b.apply(this,arguments)?f:g).call(this)}var c=new RegExp("(^|\\s+)"+d3.requote(a)+"(\\s+|$)","g");if(arguments.length<2){var d=this.node();if(e=d.classList)return e.contains(a);var e=d.className;return c.lastIndex=0,c.test(e.baseVal!=null?e.baseVal:e)}return this.each(typeof b=="function"?h:b?f:g)}function bw(a){return{__data__:a}}function bx(a){return function(){return bq(this,a)}}function by(a){return arguments.length||(a=d3.ascending),function(b,c){return a(b&&b.__data__,c&&c.__data__)}}function bA(a){return j(a,bB),a}function bC(a,b,c){j(a,bG);var d=new k,e=d3.dispatch("start","end"),f=bO;return a.id=b,a.time=c,a.tween=function(b,c){return arguments.length<2?d.get(b):(c==null?d.remove(b):d.set(b,c),a)},a.ease=function(b){return arguments.length?(f=typeof b=="function"?b:d3.ease.apply(d3,arguments),a):f},a.each=function(b,c){return arguments.length<2?bP.call(a,b):(e.on(b,c),a)},d3.timer(function(g){return a.each(function(h,i,j){function p(a){return o.active>b?r():(o.active=b,d.forEach(function(a,b){(tween=b.call(l,h,i))&&k.push(tween)}),e.start.call(l,h,i),q(a)||d3.timer(q,0,c),1)}function q(a){if(o.active!==b)return r();var c=(a-m)/n,d=f(c),g=k.length;while(g>0)k[--g].call(l,d);if(c>=1)return r(),bI=b,e.end.call(l,h,i),bI=0,1}function r(){return--o.count||delete l.__transition__,1}var k=[],l=this,m=a[j][i].delay,n=a[j][i].duration,o=l.__transition__||(l.__transition__={active:0,count:0});++o.count,m<=g?p(g):d3.timer(p,m,c)}),1},0,c),a}function bE(a,b,c){return c!=""&&bD}function bF(a,b){function d(a,d,e){var f=b.call(this,a,d);return f==null?e!=""&&bD:e!=f&&c(e,f)}function e(a,d,e){return e!=b&&c(e,b)}var c=$(a);return typeof b=="function"?d:b==null?bE:(b+="",e)}function bP(a){var b=bI,c=bO,d=bM,e=bN;bI=this.id,bO=this.ease();for(var f=0,g=this.length;f<g;f++)for(var h=this[f],i=0,j=h.length;i<j;i++){var k=h[i];k&&(bM=this[f][i].delay,bN=this[f][i].duration,a.call(k=k.node,k.__data__,i,f))}return bI=b,bO=c,bM=d,bN=e,this}function bT(){var a,b=Date.now(),c=bQ;while(c)a=b-c.then,a>=c.delay&&(c.flush=c.callback(a)),c=c.next;var d=bU()-b;d>24?(isFinite(d)&&(clearTimeout(bS),bS=setTimeout(bT,d)),bR=0):(bR=1,bV(bT))}function bU(){var a=null,b=bQ,c=Infinity;while(b)b.flush?b=a?a.next=b.next:bQ=b.next:(c=Math.min(c,b.then+b.delay),b=(a=b).next);return c}function bW(a){var b=[a.a,a.b],c=[a.c,a.d],d=bY(b),e=bX(b,c),f=bY(bZ(c,b,-e))||0;b[0]*c[1]<c[0]*b[1]&&(b[0]*=-1,b[1]*=-1,d*=-1,e*=-1),this.rotate=(d?Math.atan2(b[1],b[0]):Math.atan2(-c[0],c[1]))*b$,this.translate=[a.e,a.f],this.scale=[d,f],this.skew=f?Math.atan2(e,f)*b$:0}function bX(a,b){return a[0]*b[0]+a[1]*b[1]}function bY(a){var b=Math.sqrt(bX(a,a));return b&&(a[0]/=b,a[1]/=b),b}function bZ(a,b,c){return a[0]+=c*b[0],a[1]+=c*b[1],a}function ca(a,b){var c=a.ownerSVGElement||a;if(c.createSVGPoint){var d=c.createSVGPoint();if(b_<0&&(window.scrollX||window.scrollY)){c=d3.select(document.body).append("svg").style("position","absolute").style("top",0).style("left",0);var e=c[0][0].getScreenCTM();b_=!e.f&&!e.e,c.remove()}return b_?(d.x=b.pageX,d.y=b.pageY):(d.x=b.clientX,d.y=b.clientY),d=d.matrixTransform(a.getScreenCTM().inverse()),[d.x,d.y]}var f=a.getBoundingClientRect();return[b.clientX-f.left-a.clientLeft,b.clientY-f.top-a.clientTop]}function cb(){}function cc(a){var b=a[0],c=a[a.length-1];return b<c?[b,c]:[c,b]}function cd(a){return a.rangeExtent?a.rangeExtent():cc(a.range())}function ce(a,b){var c=0,d=a.length-1,e=a[c],f=a[d],g;f<e&&(g=c,c=d,d=g,g=e,e=f,f=g);if(g=f-e)b=b(g),a[c]=b.floor(e),a[d]=b.ceil(f);return a}function cf(){return Math}function cg(a,b,c,d){function g(){var g=Math.min(a.length,b.length)>2?cn:cm,i=d?ba:_;return e=g(a,b,i,c),f=g(b,a,i,d3.interpolate),h}function h(a){return e(a)}var e,f;return h.invert=function(a){return f(a)},h.domain=function(b){return arguments.length?(a=b.map(Number),g()):a},h.range=function(a){return arguments.length?(b=a,g()):b},h.rangeRound=function(a){return h.range(a).interpolate(d3.interpolateRound)},h.clamp=function(a){return arguments.length?(d=a,g()):d},h.interpolate=function(a){return arguments.length?(c=a,g()):c},h.ticks=function(b){return ck(a,b)},h.tickFormat=function(b){return cl(a,b)},h.nice=function(){return ce(a,ci),g()},h.copy=function(){return cg(a,b,c,d)},g()}function ch(a,b){return d3.rebind(a,b,"range","rangeRound","interpolate","clamp")}function ci(a){return a=Math.pow(10,Math.round(Math.log(a)/Math.LN10)-1),{floor:function(b){return Math.floor(b/a)*a},ceil:function(b){return Math.ceil(b/a)*a}}}function cj(a,b){var c=cc(a),d=c[1]-c[0],e=Math.pow(10,Math.floor(Math.log(d/b)/Math.LN10)),f=b/d*e;return f<=.15?e*=10:f<=.35?e*=5:f<=.75&&(e*=2),c[0]=Math.ceil(c[0]/e)*e,c[1]=Math.floor(c[1]/e)*e+e*.5,c[2]=e,c}function ck(a,b){return d3.range.apply(d3,cj(a,b))}function cl(a,b){return d3.format(",."+Math.max(0,-Math.floor(Math.log(cj(a,b)[2])/Math.LN10+.01))+"f")}function cm(a,b,c,d){var e=c(a[0],a[1]),f=d(b[0],b[1]);return function(a){return f(e(a))}}function cn(a,b,c,d){var e=[],f=[],g=0,h=Math.min(a.length,b.length)-1;a[h]<a[0]&&(a=a.slice().reverse(),b=b.slice().reverse());while(++g<=h)e.push(c(a[g-1],a[g])),f.push(d(b[g-1],b[g]));return function(b){var c=d3.bisect(a,b,1,h)-1;return f[c](e[c](b))}}function co(a,b){function d(c){return a(b(c))}var c=b.pow;return d.invert=function(b){return c(a.invert(b))},d.domain=function(e){return arguments.length?(b=e[0]<0?cr:cq,c=b.pow,a.domain(e.map(b)),d):a.domain().map(c)},d.nice=function(){return a.domain(ce(a.domain(),cf)),d},d.ticks=function(){var d=cc(a.domain()),e=[];if(d.every(isFinite)){var f=Math.floor(d[0]),g=Math.ceil(d[1]),h=c(d[0]),i=c(d[1]);if(b===cr){e.push(c(f));for(;f++<g;)for(var j=9;j>0;j--)e.push(c(f)*j)}else{for(;f<g;f++)for(var j=1;j<10;j++)e.push(c(f)*j);e.push(c(f))}for(f=0;e[f]<h;f++);for(g=e.length;e[g-1]>i;g--);e=e.slice(f,g)}return e},d.tickFormat=function(a,e){arguments.length<2&&(e=cp);if(arguments.length<1)return e;var f=a/d.ticks().length,g=b===cr?(h=-1e-12,Math.floor):(h=1e-12,Math.ceil),h;return function(a){return a/c(g(b(a)+h))<f?e(a):""}},d.copy=function(){return co(a.copy(),b)},ch(d,a)}function cq(a){return Math.log(a<0?0:a)/Math.LN10}function cr(a){return-Math.log(a>0?0:-a)/Math.LN10}function cs(a,b){function e(b){return a(c(b))}var c=ct(b),d=ct(1/b);return e.invert=function(b){return d(a.invert(b))},e.domain=function(b){return arguments.length?(a.domain(b.map(c)),e):a.domain().map(d)},e.ticks=function(a){return ck(e.domain(),a)},e.tickFormat=function(a){return cl(e.domain(),a)},e.nice=function(){return e.domain(ce(e.domain(),ci))},e.exponent=function(a){if(!arguments.length)return b;var f=e.domain();return c=ct(b=a),d=ct(1/b),e.domain(f)},e.copy=function(){return cs(a.copy(),b)},ch(e,a)}function ct(a){return function(b){return b<0?-Math.pow(-b,a):Math.pow(b,a)}}function cu(a,b){function f(b){return d[((c.get(b)||c.set(b,a.push(b)))-1)%d.length]}function g(b,c){return d3.range(a.length).map(function(a){return b+c*a})}var c,d,e;return f.domain=function(d){if(!arguments.length)return a;a=[],c=new k;var e=-1,g=d.length,h;while(++e<g)c.has(h=d[e])||c.set(h,a.push(h));return f[b.t](b.x,b.p)},f.range=function(a){return arguments.length?(d=a,e=0,b={t:"range",x:a},f):d},f.rangePoints=function(c,h){arguments.length<2&&(h=0);var i=c[0],j=c[1],k=(j-i)/(a.length-1+h);return d=g(a.length<2?(i+j)/2:i+k*h/2,k),e=0,b={t:"rangePoints",x:c,p:h},f},f.rangeBands=function(c,h){arguments.length<2&&(h=0);var i=c[1]<c[0],j=c[i-0],k=c[1-i],l=(k-j)/(a.length+h);return d=g(j+l*h,l),i&&d.reverse(),e=l*(1-h),b={t:"rangeBands",x:c,p:h},f},f.rangeRoundBands=function(c,h){arguments.length<2&&(h=0);var i=c[1]<c[0],j=c[i-0],k=c[1-i],l=Math.floor((k-j)/(a.length+h)),m=k-j-(a.length-h)*l;return d=g(j+Math.round(m/2),l),i&&d.reverse(),e=Math.round(l*(1-h)),b={t:"rangeRoundBands",x:c,p:h},f},f.rangeBand=function(){return e},f.rangeExtent=function(){return cc(b.x)},f.copy=function(){return cu(a,b)},f.domain(a)}function cz(a,b){function d(){var d=0,f=a.length,g=b.length;c=[];while(++d<g)c[d-1]=d3.quantile(a,d/g);return e}function e(a){return isNaN(a=+a)?NaN:b[d3.bisect(c,a)]}var c;return e.domain=function(b){return arguments.length?(a=b.filter(function(a){return!isNaN(a)}).sort(d3.ascending),d()):a},e.range=function(a){return arguments.length?(b=a,d()):b},e.quantiles=function(){return c},e.copy=function(){return cz(a,b)},d()}function cA(a,b,c){function f(b){return c[Math.max(0,Math.min(e,Math.floor(d*(b-a))))]}function g(){return d=c.length/(b-a),e=c.length-1,f}var d,e;return f.domain=function(c){return arguments.length?(a=+c[0],b=+c[c.length-1],g()):[a,b]},f.range=function(a){return arguments.length?(c=a,g()):c},f.copy=function(){return cA(a,b,c)},g()}function cB(a){function b(a){return+a}return b.invert=b,b.domain=b.range=function(c){return arguments.length?(a=c.map(b),b):a},b.ticks=function(b){return ck(a,b)},b.tickFormat=function(b){return cl(a,b)},b.copy=function(){return cB(a)},b}function cE(a){return a.innerRadius}function cF(a){return a.outerRadius}function cG(a){return a.startAngle}function cH(a){return a.endAngle}function cI(a){function g(d){return d.length<1?null:"M"+e(a(cJ(this,d,b,c)),f)}var b=cK,c=cL,d=cM,e=cN.get(d),f=.7;return g.x=function(a){return arguments.length?(b=a,g):b},g.y=function(a){return arguments.length?(c=a,g):c},g.interpolate=function(a){return arguments.length?(cN.has(a+="")||(a=cM),e=cN.get(d=a),g):d},g.tension=function(a){return arguments.length?(f=a,g):f},g}function cJ(a,b,c,d){var e=[],f=-1,g=b.length,h=typeof c=="function",i=typeof d=="function",j;if(h&&i)while(++f<g)e.push([c.call(a,j=b[f],f),d.call(a,j,f)]);else if(h)while(++f<g)e.push([c.call(a,b[f],f),d]);else if(i)while(++f<g)e.push([c,d.call(a,b[f],f)]);else while(++f<g)e.push([c,d]);return e}function cK(a){return a[0]}function cL(a){return a[1]}function cO(a){var b=0,c=a.length,d=a[0],e=[d[0],",",d[1]];while(++b<c)e.push("L",(d=a[b])[0],",",d[1]);return e.join("")}function cP(a){var b=0,c=a.length,d=a[0],e=[d[0],",",d[1]];while(++b<c)e.push("V",(d=a[b])[1],"H",d[0]);return e.join("")}function cQ(a){var b=0,c=a.length,d=a[0],e=[d[0],",",d[1]];while(++b<c)e.push("H",(d=a[b])[0],"V",d[1]);return e.join("")}function cR(a,b){return a.length<4?cO(a):a[1]+cU(a.slice(1,a.length-1),cV(a,b))}function cS(a,b){return a.length<3?cO(a):a[0]+cU((a.push(a[0]),a),cV([a[a.length-2]].concat(a,[a[1]]),b))}function cT(a,b,c){return a.length<3?cO(a):a[0]+cU(a,cV(a,b))}function cU(a,b){if(b.length<1||a.length!=b.length&&a.length!=b.length+2)return cO(a);var c=a.length!=b.length,d="",e=a[0],f=a[1],g=b[0],h=g,i=1;c&&(d+="Q"+(f[0]-g[0]*2/3)+","+(f[1]-g[1]*2/3)+","+f[0]+","+f[1],e=a[1],i=2);if(b.length>1){h=b[1],f=a[i],i++,d+="C"+(e[0]+g[0])+","+(e[1]+g[1])+","+(f[0]-h[0])+","+(f[1]-h[1])+","+f[0]+","+f[1];for(var j=2;j<b.length;j++,i++)f=a[i],h=b[j],d+="S"+(f[0]-h[0])+","+(f[1]-h[1])+","+f[0]+","+f[1]}if(c){var k=a[i];d+="Q"+(f[0]+h[0]*2/3)+","+(f[1]+h[1]*2/3)+","+k[0]+","+k[1]}return d}function cV(a,b){var c=[],d=(1-b)/2,e,f=a[0],g=a[1],h=1,i=a.length;while(++h<i)e=f,f=g,g=a[h],c.push([d*(g[0]-e[0]),d*(g[1]-e[1])]);return c}function cW(a){if(a.length<3)return cO(a);var b=1,c=a.length,d=a[0],e=d[0],f=d[1],g=[e,e,e,(d=a[1])[0]],h=[f,f,f,d[1]],i=[e,",",f];dc(i,g,h);while(++b<c)d=a[b],g.shift(),g.push(d[0]),h.shift(),h.push(d[1]),dc(i,g,h);b=-1;while(++b<2)g.shift(),g.push(d[0]),h.shift(),h.push(d[1]),dc(i,g,h);return i.join("")}function cX(a){if(a.length<4)return cO(a);var b=[],c=-1,d=a.length,e,f=[0],g=[0];while(++c<3)e=a[c],f.push(e[0]),g.push(e[1]);b.push(c$(db,f)+","+c$(db,g)),--c;while(++c<d)e=a[c],f.shift(),f.push(e[0]),g.shift(),g.push(e[1]),dc(b,f,g);return b.join("")}function cY(a){var b,c=-1,d=a.length,e=d+4,f,g=[],h=[];while(++c<4)f=a[c%d],g.push(f[0]),h.push(f[1]);b=[c$(db,g),",",c$(db,h)],--c;while(++c<e)f=a[c%d],g.shift(),g.push(f[0]),h.shift(),h.push(f[1]),dc(b,g,h);return b.join("")}function cZ(a,b){var c=a.length-1,d=a[0][0],e=a[0][1],f=a[c][0]-d,g=a[c][1]-e,h=-1,i,j;while(++h<=c)i=a[h],j=h/c,i[0]=b*i[0]+(1-b)*(d+j*f),i[1]=b*i[1]+(1-b)*(e+j*g);return cW(a)}function c$(a,b){return a[0]*b[0]+a[1]*b[1]+a[2]*b[2]+a[3]*b[3]}function dc(a,b,c){a.push("C",c$(c_,b),",",c$(c_,c),",",c$(da,b),",",c$(da,c),",",c$(db,b),",",c$(db,c))}function dd(a,b){return(b[1]-a[1])/(b[0]-a[0])}function de(a){var b=0,c=a.length-1,d=[],e=a[0],f=a[1],g=d[0]=dd(e,f);while(++b<c)d[b]=g+(g=dd(e=f,f=a[b+1]));return d[b]=g,d}function df(a){var b=[],c,d,e,f,g=de(a),h=-1,i=a.length-1;while(++h<i)c=dd(a[h],a[h+1]),Math.abs(c)<1e-6?g[h]=g[h+1]=0:(d=g[h]/c,e=g[h+1]/c,f=d*d+e*e,f>9&&(f=c*3/Math.sqrt(f),g[h]=f*d,g[h+1]=f*e));h=-1;while(++h<=i)f=(a[Math.min(i,h+1)][0]-a[Math.max(0,h-1)][0])/(6*(1+g[h]*g[h])),b.push([f||0,g[h]*f||0]);return b}function dg(a){return a.length<3?cO(a):a[0]+cU(a,df(a))}function dh(a){var b,c=-1,d=a.length,e,f;while(++c<d)b=a[c],e=b[0],f=b[1]+cC,b[0]=e*Math.cos(f),b[1]=e*Math.sin(f);return a}function di(a){function j(f){if(f.length<1)return null;var j=cJ(this,f,b,d),k=cJ(this,f,b===c?dj(j):c,d===e?dk(j):e);return"M"+g(a(k),i)+"L"+h(a(j.reverse()),i)+"Z"}var b=cK,c=cK,d=0,e=cL,f,g,h,i=.7;return j.x=function(a){return arguments.length?(b=c=a,j):c},j.x0=function(a){return arguments.length?(b=a,j):b},j.x1=function(a){return arguments.length?(c=a,j):c},j.y=function(a){return arguments.length?(d=e=a,j):e},j.y0=function(a){return arguments.length?(d=a,j):d},j.y1=function(a){return arguments.length?(e=a,j):e},j.interpolate=function(a){return arguments.length?(cN.has(a+="")||(a=cM),g=cN.get(f=a),h=g.reverse||g,j):f},j.tension=function(a){return arguments.length?(i=a,j):i},j.interpolate("linear")}function dj(a){return function(b,c){return a[c][0]}}function dk(a){return function(b,c){return a[c][1]}}function dl(a){return a.source}function dm(a){return a.target}function dn(a){return a.radius}function dp(a){return a.startAngle}function dq(a){return a.endAngle}function dr(a){return[a.x,a.y]}function ds(a){return function(){var b=a.apply(this,arguments),c=b[0],d=b[1]+cC;return[c*Math.cos(d),c*Math.sin(d)]}}function dt(){return 64}function du(){return"circle"}function dv(a){var b=Math.sqrt(a/Math.PI);return"M0,"+b+"A"+b+","+b+" 0 1,1 0,"+ -b+"A"+b+","+b+" 0 1,1 0,"+b+"Z"}function dz(a,b){a.attr("transform",function(a){return"translate("+b(a)+",0)"})}function dA(a,b){a.attr("transform",function(a){return"translate(0,"+b(a)+")"})}function dB(a,b,c){e=[];if(c&&b.length>1){var d=cc(a.domain()),e,f=-1,g=b.length,h=(b[1]-b[0])/++c,i,j;while(++f<g)for(i=c;--i>0;)(j=+b[f]-i*h)>=d[0]&&e.push(j);for(--f,i=0;++i<c&&(j=+b[f]+i*h)<d[1];)e.push(j)}return e}function dG(){dE||(dE=d3.select("body").append("div").style("visibility","hidden").style("top",0).style("height",0).style("width",0).style("overflow-y","scroll").append("div").style("height","2000px").node().parentNode);var a=d3.event,b;try{dE.scrollTop=1e3,dE.dispatchEvent(a),b=1e3-dE.scrollTop}catch(c){b=a.wheelDelta||-a.detail*5}return b}function dH(a){var b=a.source,c=a.target,d=dJ(b,c),e=[b];while(b!==d)b=b.parent,e.push(b);var f=e.length;while(c!==d)e.splice(f,0,c),c=c.parent;return e}function dI(a){var b=[],c=a.parent;while(c!=null)b.push(a),a=c,c=c.parent;return b.push(a),b}function dJ(a,b){if(a===b)return a;var c=dI(a),d=dI(b),e=c.pop(),f=d.pop(),g=null;while(e===f)g=e,e=c.pop(),f=d.pop();return g}function dM(a){a.fixed|=2}function dN(a){a!==dL&&(a.fixed&=1)}function dO(){dL.fixed&=1,dK=dL=null}function dP(){dL.px=d3.event.x,dL.py=d3.event.y,dK.resume()}function dQ(a,b,c){var d=0,e=0;a.charge=0;if(!a.leaf){var f=a.nodes,g=f.length,h=-1,i;while(++h<g){i=f[h];if(i==null)continue;dQ(i,b,c),a.charge+=i.charge,d+=i.charge*i.cx,e+=i.charge*i.cy}}if(a.point){a.leaf||(a.point.x+=Math.random()-.5,a.point.y+=Math.random()-.5);var j=b*c[a.point.index];a.charge+=a.pointCharge=j,d+=j*a.point.x,e+=j*a.point.y}a.cx=d/a.charge,a.cy=e/a.charge}function dR(a){return 20}function dS(a){return 1}function dU(a){return a.x}function dV(a){return a.y}function dW(a,b,c){a.y0=b,a.y=c}function dZ(a){return d3.range(a.length)}function d$(a){var b=-1,c=a[0].length,d=[];while(++b<c)d[b]=0;return d}function d_(a){var b=1,c=0,d=a[0][1],e,f=a.length;for(;b<f;++b)(e=a[b][1])>d&&(c=b,d=e);return c}function ea(a){return a.reduce(eb,0)}function eb(a,b){return a+b[1]}function ec(a,b){return ed(a,Math.ceil(Math.log(b.length)/Math.LN2+1))}function ed(a,b){var c=-1,d=+a[0],e=(a[1]-d)/b,f=[];while(++c<=b)f[c]=e*c+d;return f}function ee(a){return[d3.min(a),d3.max(a)]}function ef(a,b){return d3.rebind(a,b,"sort","children","value"),a.links=ej,a.nodes=function(b){return ek=!0,(a.nodes=a)(b)},a}function eg(a){return a.children}function eh(a){return a.value}function ei(a,b){return b.value-a.value}function ej(a){return d3.merge(a.map(function(a){return(a.children||[]).map(function(b){return{source:a,target:b}})}))}function el(a,b){return a.value-b.value}function em(a,b){var c=a._pack_next;a._pack_next=b,b._pack_prev=a,b._pack_next=c,c._pack_prev=b}function en(a,b){a._pack_next=b,b._pack_prev=a}function eo(a,b){var c=b.x-a.x,d=b.y-a.y,e=a.r+b.r;return e*e-c*c-d*d>.001}function ep(a){function l(a){b=Math.min(a.x-a.r,b),c=Math.max(a.x+a.r,c),d=Math.min(a.y-a.r,d),e=Math.max(a.y+a.r,e)}var b=Infinity,c=-Infinity,d=Infinity,e=-Infinity,f=a.length,g,h,i,j,k;a.forEach(eq),g=a[0],g.x=-g.r,g.y=0,l(g);if(f>1){h=a[1],h.x=h.r,h.y=0,l(h);if(f>2){i=a[2],eu(g,h,i),l(i),em(g,i),g._pack_prev=i,em(i,h),h=g._pack_next;for(var m=3;m<f;m++){eu(g,h,i=a[m]);var n=0,o=1,p=1;for(j=h._pack_next;j!==h;j=j._pack_next,o++)if(eo(j,i)){n=1;break}if(n==1)for(k=g._pack_prev;k!==j._pack_prev;k=k._pack_prev,p++)if(eo(k,i))break;n?(o<p||o==p&&h.r<g.r?en(g,h=j):en(g=k,h),m--):(em(g,i),h=i,l(i))}}}var q=(b+c)/2,r=(d+e)/2,s=0;for(var m=0;m<f;m++){var t=a[m];t.x-=q,t.y-=r,s=Math.max(s,t.r+Math.sqrt(t.x*t.x+t.y*t.y))}return a.forEach(er),s}function eq(a){a._pack_next=a._pack_prev=a}function er(a){delete a._pack_next,delete a._pack_prev}function es(a){var b=a.children;b&&b.length?(b.forEach(es),a.r=ep(b)):a.r=Math.sqrt(a.value)}function et(a,b,c,d){var e=a.children;a.x=b+=d*a.x,a.y=c+=d*a.y,a.r*=d;if(e){var f=-1,g=e.length;while(++f<g)et(e[f],b,c,d)}}function eu(a,b,c){var d=a.r+c.r,e=b.x-a.x,f=b.y-a.y;if(d&&(e||f)){var g=b.r+c.r,h=Math.sqrt(e*e+f*f),i=Math.max(-1,Math.min(1,(d*d+h*h-g*g)/(2*d*h))),j=Math.acos(i),k=i*(d/=h),l=Math.sin(j)*d;c.x=a.x+k*e+l*f,c.y=a.y+k*f-l*e}else c.x=a.x+d,c.y=a.y}function ev(a){return 1+d3.max(a,function(a){return a.y})}function ew(a){return a.reduce(function(a,b){return a+b.x},0)/a.length}function ex(a){var b=a.children;return b&&b.length?ex(b[0]):a}function ey(a){var b=a.children,c;return b&&(c=b.length)?ey(b[c-1]):a}function ez(a,b){return a.parent==b.parent?1:2}function eA(a){var b=a.children;return b&&b.length?b[0]:a._tree.thread}function eB(a){var b=a.children,c;return b&&(c=b.length)?b[c-1]:a._tree.thread}function eC(a,b){var c=a.children;if(c&&(e=c.length)){var d,e,f=-1;while(++f<e)b(d=eC(c[f],b),a)>0&&(a=d)}return a}function eD(a,b){return a.x-b.x}function eE(a,b){return b.x-a.x}function eF(a,b){return a.depth-b.depth}function eG(a,b){function c(a,d){var e=a.children;if(e&&(i=e.length)){var f,g=null,h=-1,i;while(++h<i)f=e[h],c(f,g),g=f}b(a,d)}c(a,null)}function eH(a){var b=0,c=0,d=a.children,e=d.length,f;while(--e>=0)f=d[e]._tree,f.prelim+=b,f.mod+=b,b+=f.shift+(c+=f.change)}function eI(a,b,c){a=a._tree,b=b._tree;var d=c/(b.number-a.number);a.change+=d,b.change-=d,b.shift+=c,b.prelim+=c,b.mod+=c}function eJ(a,b,c){return a._tree.ancestor.parent==b.parent?a._tree.ancestor:c}function eK(a){return{x:a.x,y:a.y,dx:a.dx,dy:a.dy}}function eL(a,b){var c=a.x+b[3],d=a.y+b[0],e=a.dx-b[1]-b[3],f=a.dy-b[0]-b[2];return e<0&&(c+=e/2,e=0),f<0&&(d+=f/2,f=0),{x:c,y:d,dx:e,dy:f}}function eM(a){return a.map(eN).join(",")}function eN(a){return/[",\n]/.test(a)?'"'+a.replace(/\"/g,'""')+'"':a}function eP(a,b){return function(c){return c&&a.hasOwnProperty(c.type)?a[c.type](c):b}}function eQ(a){return"m0,"+a+"a"+a+","+a+" 0 1,1 0,"+ -2*a+"a"+a+","+a+" 0 1,1 0,"+2*a+"z"}function eR(a,b){eS.hasOwnProperty(a.type)&&eS[a.type](a,b)}function eT(a,b){eR(a.geometry,b)}function eU(a,b){for(var c=a.features,d=0,e=c.length;d<e;d++)eR(c[d].geometry,b)}function eV(a,b){for(var c=a.geometries,d=0,e=c.length;d<e;d++)eR(c[d],b)}function eW(a,b){for(var c=a.coordinates,d=0,e=c.length;d<e;d++)b.apply(null,c[d])}function eX(a,b){for(var c=a.coordinates,d=0,e=c.length;d<e;d++)for(var f=c[d],g=0,h=f.length;g<h;g++)b.apply(null,f[g])}function eY(a,b){for(var c=a.coordinates,d=0,e=c.length;d<e;d++)for(var f=c[d][0],g=0,h=f.length;g<h;g++)b.apply(null,f[g])}function eZ(a,b){b.apply(null,a.coordinates)}function e$(a,b){for(var c=a.coordinates[0],d=0,e=c.length;d<e;d++)b.apply(null,c[d])}function e_(a){return a.source}function fa(a){return a.target}function fb(a,b){function q(a){var b=Math.sin(o-(a*=o))/p,c=Math.sin(a)/p,f=b*g*d+c*m*j,i=b*g*e+c*m*k,l=b*h+c*n;return[Math.atan2(i,f)/eO,Math.atan2(l,Math.sqrt(f*f+i*i))/eO]}var c=a[0]*eO,d=Math.cos(c),e=Math.sin(c),f=a[1]*eO,g=Math.cos(f),h=Math.sin(f),i=b[0]*eO,j=Math.cos(i),k=Math.sin(i),l=b[1]*eO,m=Math.cos(l),n=Math.sin(l),o=q.d=Math.acos(Math.max(-1,Math.min(1,h*n+g*m*Math.cos(i-c)))),p=Math.sin(o);return q}function fe(a){var b=0,c=0;for(;;){if(a(b,c))return[b,c];b===0?(b=c+1,c=0):(b-=1,c+=1)}}function ff(a,b,c,d){var e,f,g,h,i,j,k;return e=d[a],f=e[0],g=e[1],e=d[b],h=e[0],i=e[1],e=d[c],j=e[0],k=e[1],(k-g)*(h-f)-(i-g)*(j-f)>0}function fg(a,b,c){return(c[0]-b[0])*(a[1]-b[1])<(c[1]-b[1])*(a[0]-b[0])}function fh(a,b,c,d){var e=a[0],f=b[0],g=c[0],h=d[0],i=a[1],j=b[1],k=c[1],l=d[1],m=e-g,n=f-e,o=h-g,p=i-k,q=j-i,r=l-k,s=(o*p-r*m)/(r*n-o*q);return[e+s*n,i+s*q]}function fj(a,b){var c={list:a.map(function(a,b){return{index:b,x:a[0],y:a[1]}}).sort(function(a,b){return a.y<b.y?-1:a.y>b.y?1:a.x<b.x?-1:a.x>b.x?1:0}),bottomSite:null},d={list:[],leftEnd:null,rightEnd:null,init:function(){d.leftEnd=d.createHalfEdge(null,"l"),d.rightEnd=d.createHalfEdge(null,"l"),d.leftEnd.r=d.rightEnd,d.rightEnd.l=d.leftEnd,d.list.unshift(d.leftEnd,d.rightEnd)},createHalfEdge:function(a,b){return{edge:a,side:b,vertex:null,l:null,r:null}},insert:function(a,b){b.l=a,b.r=a.r,a.r.l=b,a.r=b},leftBound:function(a){var b=d.leftEnd;do b=b.r;while(b!=d.rightEnd&&e.rightOf(b,a));return b=b.l,b},del:function(a){a.l.r=a.r,a.r.l=a.l,a.edge=null},right:function(a){return a.r},left:function(a){return a.l},leftRegion:function(a){return a.edge==null?c.bottomSite:a.edge.region[a.side]},rightRegion:function(a){return a.edge==null?c.bottomSite:a.edge.region[fi[a.side]]}},e={bisect:function(a,b){var c={region:{l:a,r:b},ep:{l:null,r:null}},d=b.x-a.x,e=b.y-a.y,f=d>0?d:-d,g=e>0?e:-e;return c.c=a.x*d+a.y*e+(d*d+e*e)*.5,f>g?(c.a=1,c.b=e/d,c.c/=d):(c.b=1,c.a=d/e,c.c/=e),c},intersect:function(a,b){var c=a.edge,d=b.edge;if(!c||!d||c.region.r==d.region.r)return null;var e=c.a*d.b-c.b*d.a;if(Math.abs(e)<1e-10)return null;var f=(c.c*d.b-d.c*c.b)/e,g=(d.c*c.a-c.c*d.a)/e,h=c.region.r,i=d.region.r,j,k;h.y<i.y||h.y==i.y&&h.x<i.x?(j=a,k=c):(j=b,k=d);var l=f>=k.region.r.x;return l&&j.side==="l"||!l&&j.side==="r"?null:{x:f,y:g}},rightOf:function(a,b){var c=a.edge,d=c.region.r,e=b.x>d.x;if(e&&a.side==="l")return 1;if(!e&&a.side==="r")return 0;if(c.a===1){var f=b.y-d.y,g=b.x-d.x,h=0,i=0;!e&&c.b<0||e&&c.b>=0?i=h=f>=c.b*g:(i=b.x+b.y*c.b>c.c,c.b<0&&(i=!i),i||(h=1));if(!h){var j=d.x-c.region.l.x;i=c.b*(g*g-f*f)<j*f*(1+2*g/j+c.b*c.b),c.b<0&&(i=!i)}}else{var k=c.c-c.a*b.x,l=b.y-k,m=b.x-d.x,n=k-d.y;i=l*l>m*m+n*n}return a.side==="l"?i:!i},endPoint:function(a,c,d){a.ep[c]=d;if(!a.ep[fi[c]])return;b(a)},distance:function(a,b){var c=a.x-b.x,d=a.y-b.y;return Math.sqrt(c*c+d*d)}},f={list:[],insert:function(a,b,c){a.vertex=b,a.ystar=b.y+c;for(var d=0,e=f.list,g=e.length;d<g;d++){var h=e[d];if(a.ystar>h.ystar||a.ystar==h.ystar&&b.x>h.vertex.x)continue;break}e.splice(d,0,a)},del:function(a){for(var b=0,c=f.list,d=c.length;b<d&&c[b]!=a;++b);c.splice(b,1)},empty:function(){return f.list.length===0},nextEvent:function(a){for(var b=0,c=f.list,d=c.length;b<d;++b)if(c[b]==a)return c[b+1];return null},min:function(){var a=f.list[0];return{x:a.vertex.x,y:a.ystar}},extractMin:function(){return f.list.shift()}};d.init(),c.bottomSite=c.list.shift();var g=c.list.shift(),h,i,j,k,l,m,n,o,p,q,r,s,t;for(;;){f.empty()||(h=f.min());if(g&&(f.empty()||g.y<h.y||g.y==h.y&&g.x<h.x))i=d.leftBound(g),j=d.right(i),n=d.rightRegion(i),s=e.bisect(n,g),m=d.createHalfEdge(s,"l"),d.insert(i,m),q=e.intersect(i,m),q&&(f.del(i),f.insert(i,q,e.distance(q,g))),i=m,m=d.createHalfEdge(s,"r"),d.insert(i,m),q=e.intersect(m,j),q&&f.insert(m,q,e.distance(q,g)),g=c.list.shift();else if(!f.empty())i=f.extractMin(),k=d.left(i),j=d.right(i),l=d.right(j),n=d.leftRegion(i),o=d.rightRegion(j),r=i.vertex,e.endPoint(i.edge,i.side,r),e.endPoint(j.edge,j.side,r),d.del(i),f.del(j),d.del(j),t="l",n.y>o.y&&(p=n,n=o,o=p,t="r"),s=e.bisect(n,o),m=d.createHalfEdge(s,t),d.insert(k,m),e.endPoint(s,fi[t],r),q=e.intersect(k,m),q&&(f.del(k),f.insert(k,q,e.distance(q,n))),q=e.intersect(m,l),q&&f.insert(m,q,e.distance(q,n));else break}for(i=d.right(d.leftEnd);i!=d.rightEnd;i=d.right(i))b(i.edge)}function fk(){return{leaf:!0,nodes:[],point:null}}function fl(a,b,c,d,e,f){if(!a(b,c,d,e,f)){var g=(c+e)*.5,h=(d+f)*.5,i=b.nodes;i[0]&&fl(a,i[0],c,d,g,h),i[1]&&fl(a,i[1],g,d,e,h),i[2]&&fl(a,i[2],c,h,g,f),i[3]&&fl(a,i[3],g,h,e,f)}}function fm(a){return{x:a[0],y:a[1]}}function fo(){this._=new Date(arguments.length>1?Date.UTC.apply(this,arguments):arguments[0])}function fq(a,b,c,d){var e,f,g=0,h=b.length,i=c.length;while(g<h){if(d>=i)return-1;e=b.charCodeAt(g++);if(e==37){f=fw[b.charAt(g++)];if(!f||(d=f(a,c,d))<0)return-1}else if(e!=c.charCodeAt(d++))return-1}return d}function fx(a,b,c){return fz.test(b.substring(c,c+=3))?c:-1}function fy(a,b,c){fA.lastIndex=0;var d=fA.exec(b.substring(c,c+10));return d?c+=d[0].length:-1}function fB(a,b,c){var d=fC.get(b.substring(c,c+=3).toLowerCase());return d==null?-1:(a.m=d,c)}function fD(a,b,c){fE.lastIndex=0;var d=fE.exec(b.substring(c,c+12));return d?(a.m=fF.get(d[0].toLowerCase()),c+=d[0].length):-1}function fH(a,b,c){return fq(a,fv.c.toString(),b,c)}function fI(a,b,c){return fq(a,fv.x.toString(),b,c)}function fJ(a,b,c){return fq(a,fv.X.toString(),b,c)}function fK(a,b,c){fT.lastIndex=0;var d=fT.exec(b.substring(c,c+4));return d?(a.y=+d[0],c+=d[0].length):-1}function fL(a,b,c){fT.lastIndex=0;var d=fT.exec(b.substring(c,c+2));return d?(a.y=fM()+ +d[0],c+=d[0].length):-1}function fM(){return~~((new Date).getFullYear()/1e3)*1e3}function fN(a,b,c){fT.lastIndex=0;var d=fT.exec(b.substring(c,c+2));return d?(a.m=d[0]-1,c+=d[0].length):-1}function fO(a,b,c){fT.lastIndex=0;var d=fT.exec(b.substring(c,c+2));return d?(a.d=+d[0],c+=d[0].length):-1}function fP(a,b,c){fT.lastIndex=0;var d=fT.exec(b.substring(c,c+2));return d?(a.H=+d[0],c+=d[0].length):-1}function fQ(a,b,c){fT.lastIndex=0;var d=fT.exec(b.substring(c,c+2));return d?(a.M=+d[0],c+=d[0].length):-1}function fR(a,b,c){fT.lastIndex=0;var d=fT.exec(b.substring(c,c+2));return d?(a.S=+d[0],c+=d[0].length):-1}function fS(a,b,c){fT.lastIndex=0;var d=fT.exec(b.substring(c,c+3));return d?(a.L=+d[0],c+=d[0].length):-1}function fU(a,b,c){var d=fV.get(b.substring(c,c+=2).toLowerCase());return d==null?-1:(a.p=d,c)}function fW(a){var b=a.getTimezoneOffset(),c=b>0?"-":"+",d=~~(Math.abs(b)/60),e=Math.abs(b)%60;return c+fr(d)+fr(e)}function fY(a){return a.toISOString()}function fZ(a,b,c){function d(b){var c=a(b),d=f(c,1);return b-c<d-b?c:d}function e(c){return b(c=a(new fn(c-1)),1),c}function f(a,c){return b(a=new fn(+a),c),a}function g(a,d,f){var g=e(a),h=[];if(f>1)while(g<d)c(g)%f||h.push(new Date(+g)),b(g,1);else while(g<d)h.push(new Date(+g)),b(g,1);return h}function h(a,b,c){try{fn=fo;var d=new fo;return d._=a,g(d,b,c)}finally{fn=Date}}a.floor=a,a.round=d,a.ceil=e,a.offset=f,a.range=g;var i=a.utc=f$(a);return i.floor=i,i.round=f$(d),i.ceil=f$(e),i.offset=f$(f),i.range=h,a}function f$(a){return function(b,c){try{fn=fo;var d=new fo;return d._=b,a(d,c)._}finally{fn=Date}}}function f_(a,b,c){function d(b){return a(b)}return d.invert=function(b){return gb(a.invert(b))},d.domain=function(b){return arguments.length?(a.domain(b),d):a.domain().map(gb)},d.nice=function(a){var b=ga(d.domain());return d.domain([a.floor(b[0]),a.ceil(b[1])])},d.ticks=function(c,e){var f=ga(d.domain());if(typeof 
c!="function"){var g=f[1]-f[0],h=g/c,i=d3.bisect(gf,h);if(i==gf.length)return b.year(f,c);if(!i)return a.ticks(c).map(gb);Math.log(h/gf[i-1])<Math.log(gf[i]/h)&&--i,c=b[i],e=c[1],c=c[0].range}return c(f[0],new Date(+f[1]+1),e)},d.tickFormat=function(){return c},d.copy=function(){return f_(a.copy(),b,c)},d3.rebind(d,a,"range","rangeRound","interpolate","clamp")}function ga(a){var b=a[0],c=a[a.length-1];return b<c?[b,c]:[c,b]}function gb(a){return new Date(a)}function gc(a){return function(b){var c=a.length-1,d=a[c];while(!d[1](b))d=a[--c];return d[0](b)}}function gd(a){var b=new Date(a,0,1);return b.setFullYear(a),b}function ge(a){var b=a.getFullYear(),c=gd(b),d=gd(b+1);return b+(a-c)/(d-c)}function gn(a){var b=new Date(Date.UTC(a,0,1));return b.setUTCFullYear(a),b}function go(a){var b=a.getUTCFullYear(),c=gn(b),d=gn(b+1);return b+(a-c)/(d-c)}Date.now||(Date.now=function(){return+(new Date)});try{document.createElement("div").style.setProperty("opacity",0,"")}catch(a){var b=CSSStyleDeclaration.prototype,c=b.setProperty;b.setProperty=function(a,b,d){c.call(this,a,b+"",d)}}d3={version:"2.8.1"};var f=h;try{f(document.documentElement.childNodes)[0].nodeType}catch(i){f=g}var j=[].__proto__?function(a,b){a.__proto__=b}:function(a,b){for(var c in b)a[c]=b[c]};d3.map=function(a){var b=new k;for(var c in a)b.set(c,a[c]);return b},e(k,{has:function(a){return l+a in this},get:function(a){return this[l+a]},set:function(a,b){return this[l+a]=b},remove:function(a){return a=l+a,a in this&&delete this[a]},keys:function(){var a=[];return this.forEach(function(b){a.push(b)}),a},values:function(){var a=[];return this.forEach(function(b,c){a.push(c)}),a},entries:function(){var a=[];return this.forEach(function(b,c){a.push({key:b,value:c})}),a},forEach:function(a){for(var b in this)b.charCodeAt(0)===m&&a.call(this,b.substring(1),this[b])}});var l="\0",m=l.charCodeAt(0);d3.functor=function(a){return typeof a=="function"?a:function(){return a}},d3.rebind=function(a,b){var c=1,d=arguments.length,e;while(++c<d)a[e=arguments[c]]=o(a,b,b[e]);return a},d3.ascending=function(a,b){return a<b?-1:a>b?1:a>=b?0:NaN},d3.descending=function(a,b){return b<a?-1:b>a?1:b>=a?0:NaN},d3.mean=function(a,b){var c=a.length,d,e=0,f=-1,g=0;if(arguments.length===1)while(++f<c)p(d=a[f])&&(e+=(d-e)/++g);else while(++f<c)p(d=b.call(a,a[f],f))&&(e+=(d-e)/++g);return g?e:undefined},d3.median=function(a,b){return arguments.length>1&&(a=a.map(b)),a=a.filter(p),a.length?d3.quantile(a.sort(d3.ascending),.5):undefined},d3.min=function(a,b){var c=-1,d=a.length,e,f;if(arguments.length===1){while(++c<d&&((e=a[c])==null||e!=e))e=undefined;while(++c<d)(f=a[c])!=null&&e>f&&(e=f)}else{while(++c<d&&((e=b.call(a,a[c],c))==null||e!=e))e=undefined;while(++c<d)(f=b.call(a,a[c],c))!=null&&e>f&&(e=f)}return e},d3.max=function(a,b){var c=-1,d=a.length,e,f;if(arguments.length===1){while(++c<d&&((e=a[c])==null||e!=e))e=undefined;while(++c<d)(f=a[c])!=null&&f>e&&(e=f)}else{while(++c<d&&((e=b.call(a,a[c],c))==null||e!=e))e=undefined;while(++c<d)(f=b.call(a,a[c],c))!=null&&f>e&&(e=f)}return e},d3.extent=function(a,b){var c=-1,d=a.length,e,f,g;if(arguments.length===1){while(++c<d&&((e=g=a[c])==null||e!=e))e=g=undefined;while(++c<d)(f=a[c])!=null&&(e>f&&(e=f),g<f&&(g=f))}else{while(++c<d&&((e=g=b.call(a,a[c],c))==null||e!=e))e=undefined;while(++c<d)(f=b.call(a,a[c],c))!=null&&(e>f&&(e=f),g<f&&(g=f))}return[e,g]},d3.random={normal:function(a,b){return arguments.length<2&&(b=1),arguments.length<1&&(a=0),function(){var c,d,e;do c=Math.random()*2-1,d=Math.random()*2-1,e=c*c+d*d;while(!e||e>1);return a+b*c*Math.sqrt(-2*Math.log(e)/e)}}},d3.sum=function(a,b){var c=0,d=a.length,e,f=-1;if(arguments.length===1)while(++f<d)isNaN(e=+a[f])||(c+=e);else while(++f<d)isNaN(e=+b.call(a,a[f],f))||(c+=e);return c},d3.quantile=function(a,b){var c=(a.length-1)*b+1,d=Math.floor(c),e=a[d-1],f=c-d;return f?e+f*(a[d]-e):e},d3.transpose=function(a){return d3.zip.apply(d3,a)},d3.zip=function(){if(!(e=arguments.length))return[];for(var a=-1,b=d3.min(arguments,q),c=new Array(b);++a<b;)for(var d=-1,e,f=c[a]=new Array(e);++d<e;)f[d]=arguments[d][a];return c},d3.bisector=function(a){return{left:function(b,c,d,e){arguments.length<3&&(d=0),arguments.length<4&&(e=b.length);while(d<e){var f=d+e>>1;a.call(b,b[f],f)<c?d=f+1:e=f}return d},right:function(b,c,d,e){arguments.length<3&&(d=0),arguments.length<4&&(e=b.length);while(d<e){var f=d+e>>1;c<a.call(b,b[f],f)?e=f:d=f+1}return d}}};var r=d3.bisector(function(a){return a});d3.bisectLeft=r.left,d3.bisect=d3.bisectRight=r.right,d3.first=function(a,b){var c=0,d=a.length,e=a[0],f;arguments.length===1&&(b=d3.ascending);while(++c<d)b.call(a,e,f=a[c])>0&&(e=f);return e},d3.last=function(a,b){var c=0,d=a.length,e=a[0],f;arguments.length===1&&(b=d3.ascending);while(++c<d)b.call(a,e,f=a[c])<=0&&(e=f);return e},d3.nest=function(){function f(c,g){if(g>=b.length)return e?e.call(a,c):d?c.sort(d):c;var h=-1,i=c.length,j=b[g++],l,m,n=new k,o,p={};while(++h<i)(o=n.get(l=j(m=c[h])))?o.push(m):n.set(l,[m]);return n.forEach(function(a){p[a]=f(n.get(a),g)}),p}function g(a,d){if(d>=b.length)return a;var e=[],f=c[d++],h;for(h in a)e.push({key:h,values:g(a[h],d)});return f&&e.sort(function(a,b){return f(a.key,b.key)}),e}var a={},b=[],c=[],d,e;return a.map=function(a){return f(a,0)},a.entries=function(a){return g(f(a,0),0)},a.key=function(c){return b.push(c),a},a.sortKeys=function(d){return c[b.length-1]=d,a},a.sortValues=function(b){return d=b,a},a.rollup=function(b){return e=b,a},a},d3.keys=function(a){var b=[];for(var c in a)b.push(c);return b},d3.values=function(a){var b=[];for(var c in a)b.push(a[c]);return b},d3.entries=function(a){var b=[];for(var c in a)b.push({key:c,value:a[c]});return b},d3.permute=function(a,b){var c=[],d=-1,e=b.length;while(++d<e)c[d]=a[b[d]];return c},d3.merge=function(a){return Array.prototype.concat.apply([],a)},d3.split=function(a,b){var c=[],d=[],e,f=-1,g=a.length;arguments.length<2&&(b=s);while(++f<g)b.call(d,e=a[f],f)?d=[]:(d.length||c.push(d),d.push(e));return c},d3.range=function(a,b,c){arguments.length<3&&(c=1,arguments.length<2&&(b=a,a=0));if((b-a)/c===Infinity)throw new Error("infinite range");var d=[],e=u(Math.abs(c)),f=-1,g;a*=e,b*=e,c*=e;if(c<0)while((g=a+c*++f)>b)d.push(g/e);else while((g=a+c*++f)<b)d.push(g/e);return d},d3.requote=function(a){return a.replace(v,"\\$&")};var v=/[\\\^\$\*\+\?\|\[\]\(\)\.\{\}]/g;d3.round=function(a,b){return b?Math.round(a*(b=Math.pow(10,b)))/b:Math.round(a)},d3.xhr=function(a,b,c){var d=new XMLHttpRequest;arguments.length<3?(c=b,b=null):b&&d.overrideMimeType&&d.overrideMimeType(b),d.open("GET",a,!0),b&&d.setRequestHeader("Accept",b),d.onreadystatechange=function(){d.readyState===4&&c(d.status<300?d:null)},d.send(null)},d3.text=function(a,b,c){function d(a){c(a&&a.responseText)}arguments.length<3&&(c=b,b=null),d3.xhr(a,b,d)},d3.json=function(a,b){d3.text(a,"application/json",function(a){b(a?JSON.parse(a):null)})},d3.html=function(a,b){d3.text(a,"text/html",function(a){if(a!=null){var c=document.createRange();c.selectNode(document.body),a=c.createContextualFragment(a)}b(a)})},d3.xml=function(a,b,c){function d(a){c(a&&a.responseXML)}arguments.length<3&&(c=b,b=null),d3.xhr(a,b,d)};var w={svg:"http://www.w3.org/2000/svg",xhtml:"http://www.w3.org/1999/xhtml",xlink:"http://www.w3.org/1999/xlink",xml:"http://www.w3.org/XML/1998/namespace",xmlns:"http://www.w3.org/2000/xmlns/"};d3.ns={prefix:w,qualify:function(a){var b=a.indexOf(":"),c=a;return b>=0&&(c=a.substring(0,b),a=a.substring(b+1)),w.hasOwnProperty(c)?{space:w[c],local:a}:a}},d3.dispatch=function(){var a=new x,b=-1,c=arguments.length;while(++b<c)a[arguments[b]]=y(a);return a},x.prototype.on=function(a,b){var c=a.indexOf("."),d="";return c>0&&(d=a.substring(c+1),a=a.substring(0,c)),arguments.length<2?this[a].on(d):this[a].on(d,b)},d3.format=function(a){var b=z.exec(a),c=b[1]||" ",d=b[3]||"",e=b[5],f=+b[6],g=b[7],h=b[8],i=b[9],j=1,k="",l=!1;h&&(h=+h.substring(1)),e&&(c="0",g&&(f-=Math.floor((f-1)/4)));switch(i){case"n":g=!0,i="g";break;case"%":j=100,k="%",i="f";break;case"p":j=100,k="%",i="r";break;case"d":l=!0,h=0;break;case"s":j=-1,i="r"}return i=="r"&&!h&&(i="g"),i=A.get(i)||C,function(a){if(l&&a%1)return"";var b=a<0&&(a=-a)?"−":d;if(j<0){var m=d3.formatPrefix(a,h);a*=m.scale,k=m.symbol}else a*=j;a=i(a,h);if(e){var n=a.length+b.length;n<f&&(a=(new Array(f-n+1)).join(c)+a),g&&(a=D(a)),a=b+a}else{g&&(a=D(a)),a=b+a;var n=a.length;n<f&&(a=(new Array(f-n+1)).join(c)+a)}return a+k}};var z=/(?:([^{])?([<>=^]))?([+\- ])?(#)?(0)?([0-9]+)?(,)?(\.[0-9]+)?([a-zA-Z%])?/,A=d3.map({g:function(a,b){return a.toPrecision(b)},e:function(a,b){return a.toExponential(b)},f:function(a,b){return a.toFixed(b)},r:function(a,b){return d3.round(a,b=B(a,b)).toFixed(Math.max(0,Math.min(20,b)))}}),E=["y","z","a","f","p","n","μ","m","","k","M","G","T","P","E","Z","Y"].map(F);d3.formatPrefix=function(a,b){var c=0;return a&&(a<0&&(a*=-1),b&&(a=d3.round(a,B(a,b))),c=1+Math.floor(1e-12+Math.log(a)/Math.LN10),c=Math.max(-24,Math.min(24,Math.floor((c<=0?c+1:c-1)/3)*3))),E[8+c/3]};var G=P(2),H=P(3),I=function(){return O},J=d3.map({linear:I,poly:P,quad:function(){return G},cubic:function(){return H},sin:function(){return Q},exp:function(){return R},circle:function(){return S},elastic:T,back:U,bounce:function(){return V}}),K=d3.map({"in":O,out:M,"in-out":N,"out-in":function(a){return N(M(a))}});d3.ease=function(a){var b=a.indexOf("-"),c=b>=0?a.substring(0,b):a,d=b>=0?a.substring(b+1):"in";return c=J.get(c)||I,d=K.get(d)||O,L(d(c.apply(null,Array.prototype.slice.call(arguments,1))))},d3.event=null,d3.interpolate=function(a,b){var c=d3.interpolators.length,d;while(--c>=0&&!(d=d3.interpolators[c](a,b)));return d},d3.interpolateNumber=function(a,b){return b-=a,function(c){return a+b*c}},d3.interpolateRound=function(a,b){return b-=a,function(c){return Math.round(a+b*c)}},d3.interpolateString=function(a,b){var c,d,e,f=0,g=0,h=[],i=[],j,k;Z.lastIndex=0;for(d=0;c=Z.exec(b);++d)c.index&&h.push(b.substring(f,g=c.index)),i.push({i:h.length,x:c[0]}),h.push(null),f=Z.lastIndex;f<b.length&&h.push(b.substring(f));for(d=0,j=i.length;(c=Z.exec(a))&&d<j;++d){k=i[d];if(k.x==c[0]){if(k.i)if(h[k.i+1]==null){h[k.i-1]+=k.x,h.splice(k.i,1);for(e=d+1;e<j;++e)i[e].i--}else{h[k.i-1]+=k.x+h[k.i+1],h.splice(k.i,2);for(e=d+1;e<j;++e)i[e].i-=2}else if(h[k.i+1]==null)h[k.i]=k.x;else{h[k.i]=k.x+h[k.i+1],h.splice(k.i+1,1);for(e=d+1;e<j;++e)i[e].i--}i.splice(d,1),j--,d--}else k.x=d3.interpolateNumber(parseFloat(c[0]),parseFloat(k.x))}while(d<j)k=i.pop(),h[k.i+1]==null?h[k.i]=k.x:(h[k.i]=k.x+h[k.i+1],h.splice(k.i+1,1)),j--;return h.length===1?h[0]==null?i[0].x:function(){return b}:function(a){for(d=0;d<j;++d)h[(k=i[d]).i]=k.x(a);return h.join("")}},d3.interpolateTransform=function(a,b){var c=[],d=[],e,f=d3.transform(a),g=d3.transform(b),h=f.translate,i=g.translate,j=f.rotate,k=g.rotate,l=f.skew,m=g.skew,n=f.scale,o=g.scale;return h[0]!=i[0]||h[1]!=i[1]?(c.push("translate(",null,",",null,")"),d.push({i:1,x:d3.interpolateNumber(h[0],i[0])},{i:3,x:d3.interpolateNumber(h[1],i[1])})):i[0]||i[1]?c.push("translate("+i+")"):c.push(""),j!=k?d.push({i:c.push(c.pop()+"rotate(",null,")")-2,x:d3.interpolateNumber(j,k)}):k&&c.push(c.pop()+"rotate("+k+")"),l!=m?d.push({i:c.push(c.pop()+"skewX(",null,")")-2,x:d3.interpolateNumber(l,m)}):m&&c.push(c.pop()+"skewX("+m+")"),n[0]!=o[0]||n[1]!=o[1]?(e=c.push(c.pop()+"scale(",null,",",null,")"),d.push({i:e-4,x:d3.interpolateNumber(n[0],o[0])},{i:e-2,x:d3.interpolateNumber(n[1],o[1])})):(o[0]!=1||o[1]!=1)&&c.push(c.pop()+"scale("+o+")"),e=d.length,function(a){var b=-1,f;while(++b<e)c[(f=d[b]).i]=f.x(a);return c.join("")}},d3.interpolateRgb=function(a,b){a=d3.rgb(a),b=d3.rgb(b);var c=a.r,d=a.g,e=a.b,f=b.r-c,g=b.g-d,h=b.b-e;return function(a){return"#"+bd(Math.round(c+f*a))+bd(Math.round(d+g*a))+bd(Math.round(e+h*a))}},d3.interpolateHsl=function(a,b){a=d3.hsl(a),b=d3.hsl(b);var c=a.h,d=a.s,e=a.l,f=b.h-c,g=b.s-d,h=b.l-e;return function(a){return bk(c+f*a,d+g*a,e+h*a).toString()}},d3.interpolateArray=function(a,b){var c=[],d=[],e=a.length,f=b.length,g=Math.min(a.length,b.length),h;for(h=0;h<g;++h)c.push(d3.interpolate(a[h],b[h]));for(;h<e;++h)d[h]=a[h];for(;h<f;++h)d[h]=b[h];return function(a){for(h=0;h<g;++h)d[h]=c[h](a);return d}},d3.interpolateObject=function(a,b){var c={},d={},e;for(e in a)e in b?c[e]=$(e)(a[e],b[e]):d[e]=a[e];for(e in b)e in a||(d[e]=b[e]);return function(a){for(e in c)d[e]=c[e](a);return d}};var Z=/[-+]?(?:\d*\.?\d+)(?:[eE][-+]?\d+)?/g;d3.interpolators=[d3.interpolateObject,function(a,b){return b instanceof Array&&d3.interpolateArray(a,b)},function(a,b){return(typeof a=="string"||typeof b=="string")&&d3.interpolateString(a+"",b+"")},function(a,b){return(typeof b=="string"?bh.has(b)||/^(#|rgb\(|hsl\()/.test(b):b instanceof bc||b instanceof bj)&&d3.interpolateRgb(a,b)},function(a,b){return!isNaN(a=+a)&&!isNaN(b=+b)&&d3.interpolateNumber(a,b)}],d3.rgb=function(a,b,c){return arguments.length===1?a instanceof bc?bb(a.r,a.g,a.b):be(""+a,bb,bk):bb(~~a,~~b,~~c)},bc.prototype.brighter=function(a){a=Math.pow(.7,arguments.length?a:1);var b=this.r,c=this.g,d=this.b,e=30;return!b&&!c&&!d?bb(e,e,e):(b&&b<e&&(b=e),c&&c<e&&(c=e),d&&d<e&&(d=e),bb(Math.min(255,Math.floor(b/a)),Math.min(255,Math.floor(c/a)),Math.min(255,Math.floor(d/a))))},bc.prototype.darker=function(a){return a=Math.pow(.7,arguments.length?a:1),bb(Math.floor(a*this.r),Math.floor(a*this.g),Math.floor(a*this.b))},bc.prototype.hsl=function(){return bf(this.r,this.g,this.b)},bc.prototype.toString=function(){return"#"+bd(this.r)+bd(this.g)+bd(this.b)};var bh=d3.map({aliceblue:"#f0f8ff",antiquewhite:"#faebd7",aqua:"#00ffff",aquamarine:"#7fffd4",azure:"#f0ffff",beige:"#f5f5dc",bisque:"#ffe4c4",black:"#000000",blanchedalmond:"#ffebcd",blue:"#0000ff",blueviolet:"#8a2be2",brown:"#a52a2a",burlywood:"#deb887",cadetblue:"#5f9ea0",chartreuse:"#7fff00",chocolate:"#d2691e",coral:"#ff7f50",cornflowerblue:"#6495ed",cornsilk:"#fff8dc",crimson:"#dc143c",cyan:"#00ffff",darkblue:"#00008b",darkcyan:"#008b8b",darkgoldenrod:"#b8860b",darkgray:"#a9a9a9",darkgreen:"#006400",darkgrey:"#a9a9a9",darkkhaki:"#bdb76b",darkmagenta:"#8b008b",darkolivegreen:"#556b2f",darkorange:"#ff8c00",darkorchid:"#9932cc",darkred:"#8b0000",darksalmon:"#e9967a",darkseagreen:"#8fbc8f",darkslateblue:"#483d8b",darkslategray:"#2f4f4f",darkslategrey:"#2f4f4f",darkturquoise:"#00ced1",darkviolet:"#9400d3",deeppink:"#ff1493",deepskyblue:"#00bfff",dimgray:"#696969",dimgrey:"#696969",dodgerblue:"#1e90ff",firebrick:"#b22222",floralwhite:"#fffaf0",forestgreen:"#228b22",fuchsia:"#ff00ff",gainsboro:"#dcdcdc",ghostwhite:"#f8f8ff",gold:"#ffd700",goldenrod:"#daa520",gray:"#808080",green:"#008000",greenyellow:"#adff2f",grey:"#808080",honeydew:"#f0fff0",hotpink:"#ff69b4",indianred:"#cd5c5c",indigo:"#4b0082",ivory:"#fffff0",khaki:"#f0e68c",lavender:"#e6e6fa",lavenderblush:"#fff0f5",lawngreen:"#7cfc00",lemonchiffon:"#fffacd",lightblue:"#add8e6",lightcoral:"#f08080",lightcyan:"#e0ffff",lightgoldenrodyellow:"#fafad2",lightgray:"#d3d3d3",lightgreen:"#90ee90",lightgrey:"#d3d3d3",lightpink:"#ffb6c1",lightsalmon:"#ffa07a",lightseagreen:"#20b2aa",lightskyblue:"#87cefa",lightslategray:"#778899",lightslategrey:"#778899",lightsteelblue:"#b0c4de",lightyellow:"#ffffe0",lime:"#00ff00",limegreen:"#32cd32",linen:"#faf0e6",magenta:"#ff00ff",maroon:"#800000",mediumaquamarine:"#66cdaa",mediumblue:"#0000cd",mediumorchid:"#ba55d3",mediumpurple:"#9370db",mediumseagreen:"#3cb371",mediumslateblue:"#7b68ee",mediumspringgreen:"#00fa9a",mediumturquoise:"#48d1cc",mediumvioletred:"#c71585",midnightblue:"#191970",mintcream:"#f5fffa",mistyrose:"#ffe4e1",moccasin:"#ffe4b5",navajowhite:"#ffdead",navy:"#000080",oldlace:"#fdf5e6",olive:"#808000",olivedrab:"#6b8e23",orange:"#ffa500",orangered:"#ff4500",orchid:"#da70d6",palegoldenrod:"#eee8aa",palegreen:"#98fb98",paleturquoise:"#afeeee",palevioletred:"#db7093",papayawhip:"#ffefd5",peachpuff:"#ffdab9",peru:"#cd853f",pink:"#ffc0cb",plum:"#dda0dd",powderblue:"#b0e0e6",purple:"#800080",red:"#ff0000",rosybrown:"#bc8f8f",royalblue:"#4169e1",saddlebrown:"#8b4513",salmon:"#fa8072",sandybrown:"#f4a460",seagreen:"#2e8b57",seashell:"#fff5ee",sienna:"#a0522d",silver:"#c0c0c0",skyblue:"#87ceeb",slateblue:"#6a5acd",slategray:"#708090",slategrey:"#708090",snow:"#fffafa",springgreen:"#00ff7f",steelblue:"#4682b4",tan:"#d2b48c",teal:"#008080",thistle:"#d8bfd8",tomato:"#ff6347",turquoise:"#40e0d0",violet:"#ee82ee",wheat:"#f5deb3",white:"#ffffff",whitesmoke:"#f5f5f5",yellow:"#ffff00",yellowgreen:"#9acd32"});bh.forEach(function(a,b){bh.set(a,be(b,bb,bk))}),d3.hsl=function(a,b,c){return arguments.length===1?a instanceof bj?bi(a.h,a.s,a.l):be(""+a,bf,bi):bi(+a,+b,+c)},bj.prototype.brighter=function(a){return a=Math.pow(.7,arguments.length?a:1),bi(this.h,this.s,this.l/a)},bj.prototype.darker=function(a){return a=Math.pow(.7,arguments.length?a:1),bi(this.h,this.s,a*this.l)},bj.prototype.rgb=function(){return bk(this.h,this.s,this.l)},bj.prototype.toString=function(){return this.rgb().toString()};var bm=function(a,b){return b.querySelector(a)},bn=function(a,b){return b.querySelectorAll(a)},bo=document.documentElement,bp=bo.matchesSelector||bo.webkitMatchesSelector||bo.mozMatchesSelector||bo.msMatchesSelector||bo.oMatchesSelector,bq=function(a,b){return bp.call(a,b)};typeof Sizzle=="function"&&(bm=function(a,b){return Sizzle(a,b)[0]},bn=function(a,b){return Sizzle.uniqueSort(Sizzle(a,b))},bq=Sizzle.matchesSelector);var br=[];d3.selection=function(){return bz},d3.selection.prototype=br,br.select=function(a){var b=[],c,d,e,f;typeof a!="function"&&(a=bs(a));for(var g=-1,h=this.length;++g<h;){b.push(c=[]),c.parentNode=(e=this[g]).parentNode;for(var i=-1,j=e.length;++i<j;)(f=e[i])?(c.push(d=a.call(f,f.__data__,i)),d&&"__data__"in f&&(d.__data__=f.__data__)):c.push(null)}return bl(b)},br.selectAll=function(a){var b=[],c,d;typeof a!="function"&&(a=bt(a));for(var e=-1,g=this.length;++e<g;)for(var h=this[e],i=-1,j=h.length;++i<j;)if(d=h[i])b.push(c=f(a.call(d,d.__data__,i))),c.parentNode=d;return bl(b)},br.attr=function(a,b){function d(){this.removeAttribute(a)}function e(){this.removeAttributeNS(a.space,a.local)}function f(){this.setAttribute(a,b)}function g(){this.setAttributeNS(a.space,a.local,b)}function h(){var c=b.apply(this,arguments);c==null?this.removeAttribute(a):this.setAttribute(a,c)}function i(){var c=b.apply(this,arguments);c==null?this.removeAttributeNS(a.space,a.local):this.setAttributeNS(a.space,a.local,c)}a=d3.ns.qualify(a);if(arguments.length<2){var c=this.node();return a.local?c.getAttributeNS(a.space,a.local):c.getAttribute(a)}return this.each(b==null?a.local?e:d:typeof b=="function"?a.local?i:h:a.local?g:f)},br.classed=function(a,b){var c=a.split(bu),d=c.length,e=-1;if(arguments.length>1){while(++e<d)bv.call(this,c[e],b);return this}while(++e<d)if(!bv.call(this,c[e]))return!1;return!0};var bu=/\s+/g;br.style=function(a,b,c){function d(){this.style.removeProperty(a)}function e(){this.style.setProperty(a,b,c)}function f(){var d=b.apply(this,arguments);d==null?this.style.removeProperty(a):this.style.setProperty(a,d,c)}return arguments.length<3&&(c=""),arguments.length<2?window.getComputedStyle(this.node(),null).getPropertyValue(a):this.each(b==null?d:typeof b=="function"?f:e)},br.property=function(a,b){function c(){delete this[a]}function d(){this[a]=b}function e(){var c=b.apply(this,arguments);c==null?delete this[a]:this[a]=c}return arguments.length<2?this.node()[a]:this.each(b==null?c:typeof b=="function"?e:d)},br.text=function(a){return arguments.length<1?this.node().textContent:this.each(typeof a=="function"?function(){var b=a.apply(this,arguments);this.textContent=b==null?"":b}:a==null?function(){this.textContent=""}:function(){this.textContent=a})},br.html=function(a){return arguments.length<1?this.node().innerHTML:this.each(typeof a=="function"?function(){var b=a.apply(this,arguments);this.innerHTML=b==null?"":b}:a==null?function(){this.innerHTML=""}:function(){this.innerHTML=a})},br.append=function(a){function b(){return this.appendChild(document.createElementNS(this.namespaceURI,a))}function c(){return this.appendChild(document.createElementNS(a.space,a.local))}return a=d3.ns.qualify(a),this.select(a.local?c:b)},br.insert=function(a,b){function c(){return this.insertBefore(document.createElementNS(this.namespaceURI,a),bm(b,this))}function d(){return this.insertBefore(document.createElementNS(a.space,a.local),bm(b,this))}return a=d3.ns.qualify(a),this.select(a.local?d:c)},br.remove=function(){return this.each(function(){var a=this.parentNode;a&&a.removeChild(this)})},br.data=function(a,b){function g(a,c){var d,e=a.length,f=c.length,g=Math.min(e,f),l=Math.max(e,f),m=[],n=[],o=[],p,q;if(b){var r=new k,s=[],t,u=c.length;for(d=-1;++d<e;)t=b.call(p=a[d],p.__data__,d),r.has(t)?o[u++]=p:r.set(t,p),s.push(t);for(d=-1;++d<f;)t=b.call(c,q=c[d],d),r.has(t)?(m[d]=p=r.get(t),p.__data__=q,n[d]=o[d]=null):(n[d]=bw(q),m[d]=o[d]=null),r.remove(t);for(d=-1;++d<e;)r.has(s[d])&&(o[d]=a[d])}else{for(d=-1;++d<g;)p=a[d],q=c[d],p?(p.__data__=q,m[d]=p,n[d]=o[d]=null):(n[d]=bw(q),m[d]=o[d]=null);for(;d<f;++d)n[d]=bw(c[d]),m[d]=o[d]=null;for(;d<l;++d)o[d]=a[d],n[d]=m[d]=null}n.update=m,n.parentNode=m.parentNode=o.parentNode=a.parentNode,h.push(n),i.push(m),j.push(o)}var c=-1,d=this.length,e,f;if(!arguments.length){a=new Array(d=(e=this[0]).length);while(++c<d)if(f=e[c])a[c]=f.__data__;return a}var h=bA([]),i=bl([]),j=bl([]);if(typeof a=="function")while(++c<d)g(e=this[c],a.call(e,e.parentNode.__data__,c));else while(++c<d)g(e=this[c],a);return i.enter=function(){return h},i.exit=function(){return j},i},br.datum=br.map=function(a){return arguments.length<1?this.property("__data__"):this.property("__data__",a)},br.filter=function(a){var b=[],c,d,e;typeof a!="function"&&(a=bx(a));for(var f=0,g=this.length;f<g;f++){b.push(c=[]),c.parentNode=(d=this[f]).parentNode;for(var h=0,i=d.length;h<i;h++)(e=d[h])&&a.call(e,e.__data__,h)&&c.push(e)}return bl(b)},br.order=function(){for(var a=-1,b=this.length;++a<b;)for(var c=this[a],d=c.length-1,e=c[d],f;--d>=0;)if(f=c[d])e&&e!==f.nextSibling&&e.parentNode.insertBefore(f,e),e=f;return this},br.sort=function(a){a=by.apply(this,arguments);for(var b=-1,c=this.length;++b<c;)this[b].sort(a);return this.order()},br.on=function(a,b,c){arguments.length<3&&(c=!1);var d="__on"+a,e=a.indexOf(".");return e>0&&(a=a.substring(0,e)),arguments.length<2?(e=this.node()[d])&&e._:this.each(function(e,f){function i(a){var c=d3.event;d3.event=a;try{b.call(g,g.__data__,f)}finally{d3.event=c}}var g=this,h=g[d];h&&(g.removeEventListener(a,h,h.$),delete g[d]),b&&(g.addEventListener(a,g[d]=i,i.$=c),i._=b)})},br.each=function(a){for(var b=-1,c=this.length;++b<c;)for(var d=this[b],e=-1,f=d.length;++e<f;){var g=d[e];g&&a.call(g,g.__data__,e,b)}return this},br.call=function(a){return a.apply(this,(arguments[0]=this,arguments)),this},br.empty=function(){return!this.node()},br.node=function(a){for(var b=0,c=this.length;b<c;b++)for(var d=this[b],e=0,f=d.length;e<f;e++){var g=d[e];if(g)return g}return null},br.transition=function(){var a=[],b,c;for(var d=-1,e=this.length;++d<e;){a.push(b=[]);for(var f=this[d],g=-1,h=f.length;++g<h;)b.push((c=f[g])?{node:c,delay:bM,duration:bN}:null)}return bC(a,bI||++bH,Date.now())};var bz=bl([[document]]);bz[0].parentNode=bo,d3.select=function(a){return typeof a=="string"?bz.select(a):bl([[a]])},d3.selectAll=function(a){return typeof a=="string"?bz.selectAll(a):bl([f(a)])};var bB=[];d3.selection.enter=bA,d3.selection.enter.prototype=bB,bB.append=br.append,bB.insert=br.insert,bB.empty=br.empty,bB.node=br.node,bB.select=function(a){var b=[],c,d,e,f,g;for(var h=-1,i=this.length;++h<i;){e=(f=this[h]).update,b.push(c=[]),c.parentNode=f.parentNode;for(var j=-1,k=f.length;++j<k;)(g=f[j])?(c.push(e[j]=d=a.call(f.parentNode,g.__data__,j)),d.__data__=g.__data__):c.push(null)}return bl(b)};var bD={},bG=[],bH=0,bI=0,bJ=0,bK=250,bL=d3.ease("cubic-in-out"),bM=bJ,bN=bK,bO=bL;bG.call=br.call,d3.transition=function(a){return arguments.length?bI?a.transition():a:bz.transition()},d3.transition.prototype=bG,bG.select=function(a){var b=[],c,d,e;typeof a!="function"&&(a=bs(a));for(var f=-1,g=this.length;++f<g;){b.push(c=[]);for(var h=this[f],i=-1,j=h.length;++i<j;)(e=h[i])&&(d=a.call(e.node,e.node.__data__,i))?("__data__"in e.node&&(d.__data__=e.node.__data__),c.push({node:d,delay:e.delay,duration:e.duration})):c.push(null)}return bC(b,this.id,this.time).ease(this.ease())},bG.selectAll=function(a){var b=[],c,d,e;typeof a!="function"&&(a=bt(a));for(var f=-1,g=this.length;++f<g;)for(var h=this[f],i=-1,j=h.length;++i<j;)if(e=h[i]){d=a.call(e.node,e.node.__data__,i),b.push(c=[]);for(var k=-1,l=d.length;++k<l;)c.push({node:d[k],delay:e.delay,duration:e.duration})}return bC(b,this.id,this.time).ease(this.ease())},bG.attr=function(a,b){return this.attrTween(a,bF(a,b))},bG.attrTween=function(a,b){function d(a,d){var e=b.call(this,a,d,this.getAttribute(c));return e===bD?(this.removeAttribute(c),null):e&&function(a){this.setAttribute(c,e(a))}}function e(a,d){var e=b.call(this,a,d,this.getAttributeNS(c.space,c.local));return e===bD?(this.removeAttributeNS(c.space,c.local),null):e&&function(a){this.setAttributeNS(c.space,c.local,e(a))}}var c=d3.ns.qualify(a);return this.tween("attr."+a,c.local?e:d)},bG.style=function(a,b,c){return arguments.length<3&&(c=""),this.styleTween(a,bF(a,b),c)},bG.styleTween=function(a,b,c){return arguments.length<3&&(c=""),this.tween("style."+a,function(d,e){var f=b.call(this,d,e,window.getComputedStyle(this,null).getPropertyValue(a));return f===bD?(this.style.removeProperty(a),null):f&&function(b){this.style.setProperty(a,f(b),c)}})},bG.text=function(a){return this.tween("text",function(b,c){this.textContent=typeof a=="function"?a.call(this,b,c):a})},bG.remove=function(){return this.each("end.transition",function(){var a;!this.__transition__&&(a=this.parentNode)&&a.removeChild(this)})},bG.delay=function(a){var b=this;return b.each(typeof a=="function"?function(c,d,e){b[e][d].delay=a.apply(this,arguments)|0}:(a|=0,function(c,d,e){b[e][d].delay=a}))},bG.duration=function(a){var b=this;return b.each(typeof a=="function"?function(c,d,e){b[e][d].duration=Math.max(1,a.apply(this,arguments)|0)}:(a=Math.max(1,a|0),function(c,d,e){b[e][d].duration=a}))},bG.transition=function(){return this.select(n)};var bQ=null,bR,bS;d3.timer=function(a,b,c){var d=!1,e,f=bQ;if(arguments.length<3){if(arguments.length<2)b=0;else if(!isFinite(b))return;c=Date.now()}while(f){if(f.callback===a){f.then=c,f.delay=b,d=!0;break}e=f,f=f.next}d||(bQ={callback:a,then:c,delay:b,next:bQ}),bR||(bS=clearTimeout(bS),bR=1,bV(bT))},d3.timer.flush=function(){var a,b=Date.now(),c=bQ;while(c)a=b-c.then,c.delay||(c.flush=c.callback(a)),c=c.next;bU()};var bV=window.requestAnimationFrame||window.webkitRequestAnimationFrame||window.mozRequestAnimationFrame||window.oRequestAnimationFrame||window.msRequestAnimationFrame||function(a){setTimeout(a,17)};d3.transform=function(a){var b=document.createElementNS(d3.ns.prefix.svg,"g"),c={a:1,b:0,c:0,d:1,e:0,f:0};return(d3.transform=function(a){b.setAttribute("transform",a);var d=b.transform.baseVal.consolidate();return new bW(d?d.matrix:c)})(a)},bW.prototype.toString=function(){return"translate("+this.translate+")rotate("+this.rotate+")skewX("+this.skew+")scale("+this.scale+")"};var b$=180/Math.PI;d3.mouse=function(a){return ca(a,X())};var b_=/WebKit/.test(navigator.userAgent)?-1:0;d3.touches=function(a,b){return arguments.length<2&&(b=X().touches),b?f(b).map(function(b){var c=ca(a,b);return c.identifier=b.identifier,c}):[]},d3.scale={},d3.scale.linear=function(){return cg([0,1],[0,1],d3.interpolate,!1)},d3.scale.log=function(){return co(d3.scale.linear(),cq)};var cp=d3.format(".0e");cq.pow=function(a){return Math.pow(10,a)},cr.pow=function(a){return-Math.pow(10,-a)},d3.scale.pow=function(){return cs(d3.scale.linear(),1)},d3.scale.sqrt=function(){return d3.scale.pow().exponent(.5)},d3.scale.ordinal=function(){return cu([],{t:"range",x:[]})},d3.scale.category10=function(){return d3.scale.ordinal().range(cv)},d3.scale.category20=function(){return d3.scale.ordinal().range(cw)},d3.scale.category20b=function(){return d3.scale.ordinal().range(cx)},d3.scale.category20c=function(){return d3.scale.ordinal().range(cy)};var cv=["#1f77b4","#ff7f0e","#2ca02c","#d62728","#9467bd","#8c564b","#e377c2","#7f7f7f","#bcbd22","#17becf"],cw=["#1f77b4","#aec7e8","#ff7f0e","#ffbb78","#2ca02c","#98df8a","#d62728","#ff9896","#9467bd","#c5b0d5","#8c564b","#c49c94","#e377c2","#f7b6d2","#7f7f7f","#c7c7c7","#bcbd22","#dbdb8d","#17becf","#9edae5"],cx=["#393b79","#5254a3","#6b6ecf","#9c9ede","#637939","#8ca252","#b5cf6b","#cedb9c","#8c6d31","#bd9e39","#e7ba52","#e7cb94","#843c39","#ad494a","#d6616b","#e7969c","#7b4173","#a55194","#ce6dbd","#de9ed6"],cy=["#3182bd","#6baed6","#9ecae1","#c6dbef","#e6550d","#fd8d3c","#fdae6b","#fdd0a2","#31a354","#74c476","#a1d99b","#c7e9c0","#756bb1","#9e9ac8","#bcbddc","#dadaeb","#636363","#969696","#bdbdbd","#d9d9d9"];d3.scale.quantile=function(){return cz([],[])},d3.scale.quantize=function(){return cA(0,1,[0,1])},d3.scale.identity=function(){return cB([0,1])},d3.svg={},d3.svg.arc=function(){function e(){var e=a.apply(this,arguments),f=b.apply(this,arguments),g=c.apply(this,arguments)+cC,h=d.apply(this,arguments)+cC,i=(h<g&&(i=g,g=h,h=i),h-g),j=i<Math.PI?"0":"1",k=Math.cos(g),l=Math.sin(g),m=Math.cos(h),n=Math.sin(h);return i>=cD?e?"M0,"+f+"A"+f+","+f+" 0 1,1 0,"+ -f+"A"+f+","+f+" 0 1,1 0,"+f+"M0,"+e+"A"+e+","+e+" 0 1,0 0,"+ -e+"A"+e+","+e+" 0 1,0 0,"+e+"Z":"M0,"+f+"A"+f+","+f+" 0 1,1 0,"+ -f+"A"+f+","+f+" 0 1,1 0,"+f+"Z":e?"M"+f*k+","+f*l+"A"+f+","+f+" 0 "+j+",1 "+f*m+","+f*n+"L"+e*m+","+e*n+"A"+e+","+e+" 0 "+j+",0 "+e*k+","+e*l+"Z":"M"+f*k+","+f*l+"A"+f+","+f+" 0 "+j+",1 "+f*m+","+f*n+"L0,0"+"Z"}var a=cE,b=cF,c=cG,d=cH;return e.innerRadius=function(b){return arguments.length?(a=d3.functor(b),e):a},e.outerRadius=function(a){return arguments.length?(b=d3.functor(a),e):b},e.startAngle=function(a){return arguments.length?(c=d3.functor(a),e):c},e.endAngle=function(a){return arguments.length?(d=d3.functor(a),e):d},e.centroid=function(){var e=(a.apply(this,arguments)+b.apply(this,arguments))/2,f=(c.apply(this,arguments)+d.apply(this,arguments))/2+cC;return[Math.cos(f)*e,Math.sin(f)*e]},e};var cC=-Math.PI/2,cD=2*Math.PI-1e-6;d3.svg.line=function(){return cI(Object)};var cM="linear",cN=d3.map({linear:cO,"step-before":cP,"step-after":cQ,basis:cW,"basis-open":cX,"basis-closed":cY,bundle:cZ,cardinal:cT,"cardinal-open":cR,"cardinal-closed":cS,monotone:dg}),c_=[0,2/3,1/3,0],da=[0,1/3,2/3,0],db=[0,1/6,2/3,1/6];d3.svg.line.radial=function(){var a=cI(dh);return a.radius=a.x,delete a.x,a.angle=a.y,delete a.y,a},cP.reverse=cQ,cQ.reverse=cP,d3.svg.area=function(){return di(Object)},d3.svg.area.radial=function(){var a=di(dh);return a.radius=a.x,delete a.x,a.innerRadius=a.x0,delete a.x0,a.outerRadius=a.x1,delete a.x1,a.angle=a.y,delete a.y,a.startAngle=a.y0,delete a.y0,a.endAngle=a.y1,delete a.y1,a},d3.svg.chord=function(){function f(c,d){var e=g(this,a,c,d),f=g(this,b,c,d);return"M"+e.p0+i(e.r,e.p1,e.a1-e.a0)+(h(e,f)?j(e.r,e.p1,e.r,e.p0):j(e.r,e.p1,f.r,f.p0)+i(f.r,f.p1,f.a1-f.a0)+j(f.r,f.p1,e.r,e.p0))+"Z"}function g(a,b,f,g){var h=b.call(a,f,g),i=c.call(a,h,g),j=d.call(a,h,g)+cC,k=e.call(a,h,g)+cC;return{r:i,a0:j,a1:k,p0:[i*Math.cos(j),i*Math.sin(j)],p1:[i*Math.cos(k),i*Math.sin(k)]}}function h(a,b){return a.a0==b.a0&&a.a1==b.a1}function i(a,b,c){return"A"+a+","+a+" 0 "+ +(c>Math.PI)+",1 "+b}function j(a,b,c,d){return"Q 0,0 "+d}var a=dl,b=dm,c=dn,d=cG,e=cH;return f.radius=function(a){return arguments.length?(c=d3.functor(a),f):c},f.source=function(b){return arguments.length?(a=d3.functor(b),f):a},f.target=function(a){return arguments.length?(b=d3.functor(a),f):b},f.startAngle=function(a){return arguments.length?(d=d3.functor(a),f):d},f.endAngle=function(a){return arguments.length?(e=d3.functor(a),f):e},f},d3.svg.diagonal=function(){function d(d,e){var f=a.call(this,d,e),g=b.call(this,d,e),h=(f.y+g.y)/2,i=[f,{x:f.x,y:h},{x:g.x,y:h},g];return i=i.map(c),"M"+i[0]+"C"+i[1]+" "+i[2]+" "+i[3]}var a=dl,b=dm,c=dr;return d.source=function(b){return arguments.length?(a=d3.functor(b),d):a},d.target=function(a){return arguments.length?(b=d3.functor(a),d):b},d.projection=function(a){return arguments.length?(c=a,d):c},d},d3.svg.diagonal.radial=function(){var a=d3.svg.diagonal(),b=dr,c=a.projection;return a.projection=function(a){return arguments.length?c(ds(b=a)):b},a},d3.svg.mouse=d3.mouse,d3.svg.touches=d3.touches,d3.svg.symbol=function(){function c(c,d){return(dw.get(a.call(this,c,d))||dv)(b.call(this,c,d))}var a=du,b=dt;return c.type=function(b){return arguments.length?(a=d3.functor(b),c):a},c.size=function(a){return arguments.length?(b=d3.functor(a),c):b},c};var dw=d3.map({circle
:dv,cross:function(a){var b=Math.sqrt(a/5)/2;return"M"+ -3*b+","+ -b+"H"+ -b+"V"+ -3*b+"H"+b+"V"+ -b+"H"+3*b+"V"+b+"H"+b+"V"+3*b+"H"+ -b+"V"+b+"H"+ -3*b+"Z"},diamond:function(a){var b=Math.sqrt(a/(2*dy)),c=b*dy;return"M0,"+ -b+"L"+c+",0"+" 0,"+b+" "+ -c+",0"+"Z"},square:function(a){var b=Math.sqrt(a)/2;return"M"+ -b+","+ -b+"L"+b+","+ -b+" "+b+","+b+" "+ -b+","+b+"Z"},"triangle-down":function(a){var b=Math.sqrt(a/dx),c=b*dx/2;return"M0,"+c+"L"+b+","+ -c+" "+ -b+","+ -c+"Z"},"triangle-up":function(a){var b=Math.sqrt(a/dx),c=b*dx/2;return"M0,"+ -c+"L"+b+","+c+" "+ -b+","+c+"Z"}});d3.svg.symbolTypes=dw.keys();var dx=Math.sqrt(3),dy=Math.tan(30*Math.PI/180);d3.svg.axis=function(){function k(k){k.each(function(){var k=d3.select(this),l=h==null?a.ticks?a.ticks.apply(a,g):a.domain():h,m=i==null?a.tickFormat?a.tickFormat.apply(a,g):String:i,n=dB(a,l,j),o=k.selectAll(".minor").data(n,String),p=o.enter().insert("line","g").attr("class","tick minor").style("opacity",1e-6),q=d3.transition(o.exit()).style("opacity",1e-6).remove(),r=d3.transition(o).style("opacity",1),s=k.selectAll("g").data(l,String),t=s.enter().insert("g","path").style("opacity",1e-6),u=d3.transition(s.exit()).style("opacity",1e-6).remove(),v=d3.transition(s).style("opacity",1),w,x=cd(a),y=k.selectAll(".domain").data([0]),z=y.enter().append("path").attr("class","domain"),A=d3.transition(y),B=a.copy(),C=this.__chart__||B;this.__chart__=B,t.append("line").attr("class","tick"),t.append("text"),v.select("text").text(m);switch(b){case"bottom":w=dz,p.attr("y2",d),r.attr("x2",0).attr("y2",d),t.select("line").attr("y2",c),t.select("text").attr("y",Math.max(c,0)+f),v.select("line").attr("x2",0).attr("y2",c),v.select("text").attr("x",0).attr("y",Math.max(c,0)+f).attr("dy",".71em").attr("text-anchor","middle"),A.attr("d","M"+x[0]+","+e+"V0H"+x[1]+"V"+e);break;case"top":w=dz,p.attr("y2",-d),r.attr("x2",0).attr("y2",-d),t.select("line").attr("y2",-c),t.select("text").attr("y",-(Math.max(c,0)+f)),v.select("line").attr("x2",0).attr("y2",-c),v.select("text").attr("x",0).attr("y",-(Math.max(c,0)+f)).attr("dy","0em").attr("text-anchor","middle"),A.attr("d","M"+x[0]+","+ -e+"V0H"+x[1]+"V"+ -e);break;case"left":w=dA,p.attr("x2",-d),r.attr("x2",-d).attr("y2",0),t.select("line").attr("x2",-c),t.select("text").attr("x",-(Math.max(c,0)+f)),v.select("line").attr("x2",-c).attr("y2",0),v.select("text").attr("x",-(Math.max(c,0)+f)).attr("y",0).attr("dy",".32em").attr("text-anchor","end"),A.attr("d","M"+ -e+","+x[0]+"H0V"+x[1]+"H"+ -e);break;case"right":w=dA,p.attr("x2",d),r.attr("x2",d).attr("y2",0),t.select("line").attr("x2",c),t.select("text").attr("x",Math.max(c,0)+f),v.select("line").attr("x2",c).attr("y2",0),v.select("text").attr("x",Math.max(c,0)+f).attr("y",0).attr("dy",".32em").attr("text-anchor","start"),A.attr("d","M"+e+","+x[0]+"H0V"+x[1]+"H"+e)}if(a.ticks)t.call(w,C),v.call(w,B),u.call(w,B),p.call(w,C),r.call(w,B),q.call(w,B);else{var D=B.rangeBand()/2,E=function(a){return B(a)+D};t.call(w,E),v.call(w,E)}})}var a=d3.scale.linear(),b="bottom",c=6,d=6,e=6,f=3,g=[10],h=null,i,j=0;return k.scale=function(b){return arguments.length?(a=b,k):a},k.orient=function(a){return arguments.length?(b=a,k):b},k.ticks=function(){return arguments.length?(g=arguments,k):g},k.tickValues=function(a){return arguments.length?(h=a,k):h},k.tickFormat=function(a){return arguments.length?(i=a,k):i},k.tickSize=function(a,b,f){if(!arguments.length)return c;var g=arguments.length-1;return c=+a,d=g>1?+b:c,e=g>0?+arguments[g]:c,k},k.tickPadding=function(a){return arguments.length?(f=+a,k):f},k.tickSubdivide=function(a){return arguments.length?(j=+a,k):j},k},d3.svg.brush=function(){function g(a){a.each(function(){var a=d3.select(this),e=a.selectAll(".background").data([0]),f=a.selectAll(".extent").data([0]),l=a.selectAll(".resize").data(d,String),m;a.style("pointer-events","all").on("mousedown.brush",k).on("touchstart.brush",k),e.enter().append("rect").attr("class","background").style("visibility","hidden").style("cursor","crosshair"),f.enter().append("rect").attr("class","extent").style("cursor","move"),l.enter().append("g").attr("class",function(a){return"resize "+a}).style("cursor",function(a){return dC[a]}).append("rect").attr("x",function(a){return/[ew]$/.test(a)?-3:null}).attr("y",function(a){return/^[ns]/.test(a)?-3:null}).attr("width",6).attr("height",6).style("visibility","hidden"),l.style("display",g.empty()?"none":null),l.exit().remove(),b&&(m=cd(b),e.attr("x",m[0]).attr("width",m[1]-m[0]),i(a)),c&&(m=cd(c),e.attr("y",m[0]).attr("height",m[1]-m[0]),j(a)),h(a)})}function h(a){a.selectAll(".resize").attr("transform",function(a){return"translate("+e[+/e$/.test(a)][0]+","+e[+/^s/.test(a)][1]+")"})}function i(a){a.select(".extent").attr("x",e[0][0]),a.selectAll(".extent,.n>rect,.s>rect").attr("width",e[1][0]-e[0][0])}function j(a){a.select(".extent").attr("y",e[0][1]),a.selectAll(".extent,.e>rect,.w>rect").attr("height",e[1][1]-e[0][1])}function k(){function x(){var a=d3.event.changedTouches;return a?d3.touches(d,a)[0]:d3.mouse(d)}function y(){d3.event.keyCode==32&&(q||(r=null,s[0]-=e[1][0],s[1]-=e[1][1],q=2),W())}function z(){d3.event.keyCode==32&&q==2&&(s[0]+=e[1][0],s[1]+=e[1][1],q=0,W())}function A(){var a=x(),d=!1;t&&(a[0]+=t[0],a[1]+=t[1]),q||(d3.event.altKey?(r||(r=[(e[0][0]+e[1][0])/2,(e[0][1]+e[1][1])/2]),s[0]=e[+(a[0]<r[0])][0],s[1]=e[+(a[1]<r[1])][1]):r=null),o&&B(a,b,0)&&(i(m),d=!0),p&&B(a,c,1)&&(j(m),d=!0),d&&(h(m),l({type:"brush",mode:q?"move":"resize"}))}function B(a,b,c){var d=cd(b),g=d[0],h=d[1],i=s[c],j=e[1][c]-e[0][c],k,l;q&&(g-=i,h-=j+i),k=Math.max(g,Math.min(h,a[c])),q?l=(k+=i)+j:(r&&(i=Math.max(g,Math.min(h,2*r[c]-k))),i<k?(l=k,k=i):l=i);if(e[0][c]!==k||e[1][c]!==l)return f=null,e[0][c]=k,e[1][c]=l,!0}function C(){A(),m.style("pointer-events","all").selectAll(".resize").style("display",g.empty()?"none":null),d3.select("body").style("cursor",null),u.on("mousemove.brush",null).on("mouseup.brush",null).on("touchmove.brush",null).on("touchend.brush",null).on("keydown.brush",null).on("keyup.brush",null),l({type:"brushend"}),W()}var d=this,k=d3.select(d3.event.target),l=a.of(d,arguments),m=d3.select(d),n=k.datum(),o=!/^(n|s)$/.test(n)&&b,p=!/^(e|w)$/.test(n)&&c,q=k.classed("extent"),r,s=x(),t,u=d3.select(window).on("mousemove.brush",A).on("mouseup.brush",C).on("touchmove.brush",A).on("touchend.brush",C).on("keydown.brush",y).on("keyup.brush",z);if(q)s[0]=e[0][0]-s[0],s[1]=e[0][1]-s[1];else if(n){var v=+/w$/.test(n),w=+/^n/.test(n);t=[e[1-v][0]-s[0],e[1-w][1]-s[1]],s[0]=e[v][0],s[1]=e[w][1]}else d3.event.altKey&&(r=s.slice());m.style("pointer-events","none").selectAll(".resize").style("display",null),d3.select("body").style("cursor",k.style("cursor")),l({type:"brushstart"}),A(),W()}var a=Y(g,"brushstart","brush","brushend"),b=null,c=null,d=dD[0],e=[[0,0],[0,0]],f;return g.x=function(a){return arguments.length?(b=a,d=dD[!b<<1|!c],g):b},g.y=function(a){return arguments.length?(c=a,d=dD[!b<<1|!c],g):c},g.extent=function(a){var d,h,i,j,k;return arguments.length?(f=[[0,0],[0,0]],b&&(d=a[0],h=a[1],c&&(d=d[0],h=h[0]),f[0][0]=d,f[1][0]=h,b.invert&&(d=b(d),h=b(h)),h<d&&(k=d,d=h,h=k),e[0][0]=d|0,e[1][0]=h|0),c&&(i=a[0],j=a[1],b&&(i=i[1],j=j[1]),f[0][1]=i,f[1][1]=j,c.invert&&(i=c(i),j=c(j)),j<i&&(k=i,i=j,j=k),e[0][1]=i|0,e[1][1]=j|0),g):(a=f||e,b&&(d=a[0][0],h=a[1][0],f||(d=e[0][0],h=e[1][0],b.invert&&(d=b.invert(d),h=b.invert(h)),h<d&&(k=d,d=h,h=k))),c&&(i=a[0][1],j=a[1][1],f||(i=e[0][1],j=e[1][1],c.invert&&(i=c.invert(i),j=c.invert(j)),j<i&&(k=i,i=j,j=k))),b&&c?[[d,i],[h,j]]:b?[d,h]:c&&[i,j])},g.clear=function(){return f=null,e[0][0]=e[0][1]=e[1][0]=e[1][1]=0,g},g.empty=function(){return b&&e[0][0]===e[1][0]||c&&e[0][1]===e[1][1]},d3.rebind(g,a,"on")};var dC={n:"ns-resize",e:"ew-resize",s:"ns-resize",w:"ew-resize",nw:"nwse-resize",ne:"nesw-resize",se:"nwse-resize",sw:"nesw-resize"},dD=[["n","e","s","w","nw","ne","se","sw"],["e","w"],["n","s"],[]];d3.behavior={},d3.behavior.drag=function(){function c(){this.on("mousedown.drag",d).on("touchstart.drag",d)}function d(){function j(){var a=c.parentNode,b=d3.event.changedTouches;return b?d3.touches(a,b)[0]:d3.mouse(a)}function k(){if(!c.parentNode)return l();var a=j(),b=a[0]-g[0],e=a[1]-g[1];h|=b|e,g=a,W(),d({type:"drag",x:a[0]+f[0],y:a[1]+f[1],dx:b,dy:e})}function l(){d({type:"dragend"}),h&&(W(),d3.event.target===e&&i.on("click.drag",m,!0)),i.on("mousemove.drag",null).on("touchmove.drag",null).on("mouseup.drag",null).on("touchend.drag",null)}function m(){W(),i.on("click.drag",null)}var c=this,d=a.of(c,arguments),e=d3.event.target,f,g=j(),h=0,i=d3.select(window).on("mousemove.drag",k).on("touchmove.drag",k).on("mouseup.drag",l,!0).on("touchend.drag",l,!0);b?(f=b.apply(c,arguments),f=[f.x-g[0],f.y-g[1]]):f=[0,0],d({type:"dragstart"})}var a=Y(c,"drag","dragstart","dragend"),b=null;return c.origin=function(a){return arguments.length?(b=a,c):b},d3.rebind(c,a,"on")},d3.behavior.zoom=function(){function l(){this.on("mousedown.zoom",r).on("mousewheel.zoom",s).on("mousemove.zoom",t).on("DOMMouseScroll.zoom",s).on("dblclick.zoom",u).on("touchstart.zoom",v).on("touchmove.zoom",w).on("touchend.zoom",v)}function m(b){return[(b[0]-a[0])/c,(b[1]-a[1])/c]}function n(b){return[b[0]*c+a[0],b[1]*c+a[1]]}function o(a){c=Math.max(e[0],Math.min(e[1],a))}function p(b,c){c=n(c),a[0]+=b[0]-c[0],a[1]+=b[1]-c[1]}function q(b){h&&h.domain(g.range().map(function(b){return(b-a[0])/c}).map(g.invert)),j&&j.domain(i.range().map(function(b){return(b-a[1])/c}).map(i.invert)),d3.event.preventDefault(),b({type:"zoom",scale:c,translate:a})}function r(){function h(){d=1,p(d3.mouse(a),g),q(b)}function i(){d&&W(),e.on("mousemove.zoom",null).on("mouseup.zoom",null),d&&d3.event.target===c&&e.on("click.zoom",j)}function j(){W(),e.on("click.zoom",null)}var a=this,b=f.of(a,arguments),c=d3.event.target,d=0,e=d3.select(window).on("mousemove.zoom",h).on("mouseup.zoom",i),g=m(d3.mouse(a));window.focus(),W()}function s(){b||(b=m(d3.mouse(this))),o(Math.pow(2,dG()*.002)*c),p(d3.mouse(this),b),q(f.of(this,arguments))}function t(){b=null}function u(){var a=d3.mouse(this),b=m(a);o(d3.event.shiftKey?c/2:c*2),p(a,b),q(f.of(this,arguments))}function v(){var a=d3.touches(this),e=Date.now();d=c,b={},a.forEach(function(a){b[a.identifier]=m(a)}),W();if(a.length===1&&e-k<500){var g=a[0],h=m(a[0]);o(c*2),p(g,h),q(f.of(this,arguments))}k=e}function w(){var a=d3.touches(this),c=a[0],e=b[c.identifier];if(g=a[1]){var g,h=b[g.identifier];c=[(c[0]+g[0])/2,(c[1]+g[1])/2],e=[(e[0]+h[0])/2,(e[1]+h[1])/2],o(d3.event.scale*d)}p(c,e),q(f.of(this,arguments))}var a=[0,0],b,c=1,d,e=dF,f=Y(l,"zoom"),g,h,i,j,k;return l.translate=function(b){return arguments.length?(a=b.map(Number),l):a},l.scale=function(a){return arguments.length?(c=+a,l):c},l.scaleExtent=function(a){return arguments.length?(e=a==null?dF:a.map(Number),l):e},l.x=function(a){return arguments.length?(h=a,g=a.copy(),l):h},l.y=function(a){return arguments.length?(j=a,i=a.copy(),l):j},d3.rebind(l,f,"on")};var dE,dF=[0,Infinity];d3.layout={},d3.layout.bundle=function(){return function(a){var b=[],c=-1,d=a.length;while(++c<d)b.push(dH(a[c]));return b}},d3.layout.chord=function(){function j(){var a={},j=[],l=d3.range(e),m=[],n,o,p,q,r;b=[],c=[],n=0,q=-1;while(++q<e){o=0,r=-1;while(++r<e)o+=d[q][r];j.push(o),m.push(d3.range(e)),n+=o}g&&l.sort(function(a,b){return g(j[a],j[b])}),h&&m.forEach(function(a,b){a.sort(function(a,c){return h(d[b][a],d[b][c])})}),n=(2*Math.PI-f*e)/n,o=0,q=-1;while(++q<e){p=o,r=-1;while(++r<e){var s=l[q],t=m[s][r],u=d[s][t],v=o,w=o+=u*n;a[s+"-"+t]={index:s,subindex:t,startAngle:v,endAngle:w,value:u}}c.push({index:s,startAngle:p,endAngle:o,value:(o-p)/n}),o+=f}q=-1;while(++q<e){r=q-1;while(++r<e){var x=a[q+"-"+r],y=a[r+"-"+q];(x.value||y.value)&&b.push(x.value<y.value?{source:y,target:x}:{source:x,target:y})}}i&&k()}function k(){b.sort(function(a,b){return i((a.source.value+a.target.value)/2,(b.source.value+b.target.value)/2)})}var a={},b,c,d,e,f=0,g,h,i;return a.matrix=function(f){return arguments.length?(e=(d=f)&&d.length,b=c=null,a):d},a.padding=function(d){return arguments.length?(f=d,b=c=null,a):f},a.sortGroups=function(d){return arguments.length?(g=d,b=c=null,a):g},a.sortSubgroups=function(c){return arguments.length?(h=c,b=null,a):h},a.sortChords=function(c){return arguments.length?(i=c,b&&k(),a):i},a.chords=function(){return b||j(),b},a.groups=function(){return c||j(),c},a},d3.layout.force=function(){function r(a){return function(b,c,d,e,f){if(b.point!==a){var g=b.cx-a.x,h=b.cy-a.y,i=1/Math.sqrt(g*g+h*h);if((e-c)*i<k){var j=b.charge*i*i;return a.px-=g*j,a.py-=h*j,!0}if(b.point&&isFinite(i)){var j=b.pointCharge*i*i;a.px-=g*j,a.py-=h*j}}return!b.charge}}function s(b){dM(dL=b),dK=a}var a={},b=d3.dispatch("start","tick","end"),c=[1,1],d,e,f=.9,g=dR,h=dS,i=-30,j=.1,k=.8,l,m=[],n=[],o,p,q;return a.tick=function(){if((e*=.99)<.005)return b.end({type:"end",alpha:e=0}),!0;var a=m.length,d=n.length,g,h,k,l,s,t,u,v,w;for(h=0;h<d;++h){k=n[h],l=k.source,s=k.target,v=s.x-l.x,w=s.y-l.y;if(t=v*v+w*w)t=e*p[h]*((t=Math.sqrt(t))-o[h])/t,v*=t,w*=t,s.x-=v*(u=l.weight/(s.weight+l.weight)),s.y-=w*u,l.x+=v*(u=1-u),l.y+=w*u}if(u=e*j){v=c[0]/2,w=c[1]/2,h=-1;if(u)while(++h<a)k=m[h],k.x+=(v-k.x)*u,k.y+=(w-k.y)*u}if(i){dQ(g=d3.geom.quadtree(m),e,q),h=-1;while(++h<a)(k=m[h]).fixed||g.visit(r(k))}h=-1;while(++h<a)k=m[h],k.fixed?(k.x=k.px,k.y=k.py):(k.x-=(k.px-(k.px=k.x))*f,k.y-=(k.py-(k.py=k.y))*f);b.tick({type:"tick",alpha:e})},a.nodes=function(b){return arguments.length?(m=b,a):m},a.links=function(b){return arguments.length?(n=b,a):n},a.size=function(b){return arguments.length?(c=b,a):c},a.linkDistance=function(b){return arguments.length?(g=d3.functor(b),a):g},a.distance=a.linkDistance,a.linkStrength=function(b){return arguments.length?(h=d3.functor(b),a):h},a.friction=function(b){return arguments.length?(f=b,a):f},a.charge=function(b){return arguments.length?(i=typeof b=="function"?b:+b,a):i},a.gravity=function(b){return arguments.length?(j=b,a):j},a.theta=function(b){return arguments.length?(k=b,a):k},a.alpha=function(c){return arguments.length?(e?c>0?e=c:e=0:c>0&&(b.start({type:"start",alpha:e=c}),d3.timer(a.tick)),a):e},a.start=function(){function s(a,c){var d=t(b),e=-1,f=d.length,g;while(++e<f)if(!isNaN(g=d[e][a]))return g;return Math.random()*c}function t(){if(!l){l=[];for(d=0;d<e;++d)l[d]=[];for(d=0;d<f;++d){var a=n[d];l[a.source.index].push(a.target),l[a.target.index].push(a.source)}}return l[b]}var b,d,e=m.length,f=n.length,j=c[0],k=c[1],l,r;for(b=0;b<e;++b)(r=m[b]).index=b,r.weight=0;o=[],p=[];for(b=0;b<f;++b)r=n[b],typeof r.source=="number"&&(r.source=m[r.source]),typeof r.target=="number"&&(r.target=m[r.target]),o[b]=g.call(this,r,b),p[b]=h.call(this,r,b),++r.source.weight,++r.target.weight;for(b=0;b<e;++b)r=m[b],isNaN(r.x)&&(r.x=s("x",j)),isNaN(r.y)&&(r.y=s("y",k)),isNaN(r.px)&&(r.px=r.x),isNaN(r.py)&&(r.py=r.y);q=[];if(typeof i=="function")for(b=0;b<e;++b)q[b]=+i.call(this,m[b],b);else for(b=0;b<e;++b)q[b]=i;return a.resume()},a.resume=function(){return a.alpha(.1)},a.stop=function(){return a.alpha(0)},a.drag=function(){d||(d=d3.behavior.drag().origin(Object).on("dragstart",s).on("drag",dP).on("dragend",dO)),this.on("mouseover.force",dM).on("mouseout.force",dN).call(d)},d3.rebind(a,b,"on")};var dK,dL;d3.layout.partition=function(){function c(a,b,d,e){var f=a.children;a.x=b,a.y=a.depth*e,a.dx=d,a.dy=e;if(f&&(h=f.length)){var g=-1,h,i,j;d=a.value?d/a.value:0;while(++g<h)c(i=f[g],b,j=i.value*d,e),b+=j}}function d(a){var b=a.children,c=0;if(b&&(f=b.length)){var e=-1,f;while(++e<f)c=Math.max(c,d(b[e]))}return 1+c}function e(e,f){var g=a.call(this,e,f);return c(g[0],0,b[0],b[1]/d(g[0])),g}var a=d3.layout.hierarchy(),b=[1,1];return e.size=function(a){return arguments.length?(b=a,e):b},ef(e,a)},d3.layout.pie=function(){function f(g,h){var i=g.map(function(b,c){return+a.call(f,b,c)}),j=+(typeof c=="function"?c.apply(this,arguments):c),k=((typeof e=="function"?e.apply(this,arguments):e)-c)/d3.sum(i),l=d3.range(g.length);b!=null&&l.sort(b===dT?function(a,b){return i[b]-i[a]}:function(a,c){return b(g[a],g[c])});var m=[];return l.forEach(function(a){m[a]={data:g[a],value:d=i[a],startAngle:j,endAngle:j+=d*k}}),m}var a=Number,b=dT,c=0,e=2*Math.PI;return f.value=function(b){return arguments.length?(a=b,f):a},f.sort=function(a){return arguments.length?(b=a,f):b},f.startAngle=function(a){return arguments.length?(c=a,f):c},f.endAngle=function(a){return arguments.length?(e=a,f):e},f};var dT={};d3.layout.stack=function(){function g(h,i){var j=h.map(function(b,c){return a.call(g,b,c)}),k=j.map(function(a,b){return a.map(function(a,b){return[e.call(g,a,b),f.call(g,a,b)]})}),l=b.call(g,k,i);j=d3.permute(j,l),k=d3.permute(k,l);var m=c.call(g,k,i),n=j.length,o=j[0].length,p,q,r;for(q=0;q<o;++q){d.call(g,j[0][q],r=m[q],k[0][q][1]);for(p=1;p<n;++p)d.call(g,j[p][q],r+=k[p-1][q][1],k[p][q][1])}return h}var a=Object,b=dZ,c=d$,d=dW,e=dU,f=dV;return g.values=function(b){return arguments.length?(a=b,g):a},g.order=function(a){return arguments.length?(b=typeof a=="function"?a:dX.get(a)||dZ,g):b},g.offset=function(a){return arguments.length?(c=typeof a=="function"?a:dY.get(a)||d$,g):c},g.x=function(a){return arguments.length?(e=a,g):e},g.y=function(a){return arguments.length?(f=a,g):f},g.out=function(a){return arguments.length?(d=a,g):d},g};var dX=d3.map({"inside-out":function(a){var b=a.length,c,d,e=a.map(d_),f=a.map(ea),g=d3.range(b).sort(function(a,b){return e[a]-e[b]}),h=0,i=0,j=[],k=[];for(c=0;c<b;++c)d=g[c],h<i?(h+=f[d],j.push(d)):(i+=f[d],k.push(d));return k.reverse().concat(j)},reverse:function(a){return d3.range(a.length).reverse()},"default":dZ}),dY=d3.map({silhouette:function(a){var b=a.length,c=a[0].length,d=[],e=0,f,g,h,i=[];for(g=0;g<c;++g){for(f=0,h=0;f<b;f++)h+=a[f][g][1];h>e&&(e=h),d.push(h)}for(g=0;g<c;++g)i[g]=(e-d[g])/2;return i},wiggle:function(a){var b=a.length,c=a[0],d=c.length,e=0,f,g,h,i,j,k,l,m,n,o=[];o[0]=m=n=0;for(g=1;g<d;++g){for(f=0,i=0;f<b;++f)i+=a[f][g][1];for(f=0,j=0,l=c[g][0]-c[g-1][0];f<b;++f){for(h=0,k=(a[f][g][1]-a[f][g-1][1])/(2*l);h<f;++h)k+=(a[h][g][1]-a[h][g-1][1])/l;j+=k*a[f][g][1]}o[g]=m-=i?j/i*l:0,m<n&&(n=m)}for(g=0;g<d;++g)o[g]-=n;return o},expand:function(a){var b=a.length,c=a[0].length,d=1/b,e,f,g,h=[];for(f=0;f<c;++f){for(e=0,g=0;e<b;e++)g+=a[e][f][1];if(g)for(e=0;e<b;e++)a[e][f][1]/=g;else for(e=0;e<b;e++)a[e][f][1]=d}for(f=0;f<c;++f)h[f]=0;return h},zero:d$});d3.layout.histogram=function(){function e(e,f){var g=[],h=e.map(b,this),i=c.call(this,h,f),j=d.call(this,i,h,f),k,f=-1,l=h.length,m=j.length-1,n=a?1:1/l,o;while(++f<m)k=g[f]=[],k.dx=j[f+1]-(k.x=j[f]),k.y=0;f=-1;while(++f<l)o=h[f],o>=i[0]&&o<=i[1]&&(k=g[d3.bisect(j,o,1,m)-1],k.y+=n,k.push(e[f]));return g}var a=!0,b=Number,c=ee,d=ec;return e.value=function(a){return arguments.length?(b=a,e):b},e.range=function(a){return arguments.length?(c=d3.functor(a),e):c},e.bins=function(a){return arguments.length?(d=typeof a=="number"?function(b){return ed(b,a)}:d3.functor(a),e):d},e.frequency=function(b){return arguments.length?(a=!!b,e):a},e},d3.layout.hierarchy=function(){function e(f,h,i){var j=b.call(g,f,h),k=ek?f:{data:f};k.depth=h,i.push(k);if(j&&(m=j.length)){var l=-1,m,n=k.children=[],o=0,p=h+1;while(++l<m)d=e(j[l],p,i),d.parent=k,n.push(d),o+=d.value;a&&n.sort(a),c&&(k.value=o)}else c&&(k.value=+c.call(g,f,h)||0);return k}function f(a,b){var d=a.children,e=0;if(d&&(i=d.length)){var h=-1,i,j=b+1;while(++h<i)e+=f(d[h],j)}else c&&(e=+c.call(g,ek?a:a.data,b)||0);return c&&(a.value=e),e}function g(a){var b=[];return e(a,0,b),b}var a=ei,b=eg,c=eh;return g.sort=function(b){return arguments.length?(a=b,g):a},g.children=function(a){return arguments.length?(b=a,g):b},g.value=function(a){return arguments.length?(c=a,g):c},g.revalue=function(a){return f(a,0),a},g};var ek=!1;d3.layout.pack=function(){function c(c,d){var e=a.call(this,c,d),f=e[0];f.x=0,f.y=0,es(f);var g=b[0],h=b[1],i=1/Math.max(2*f.r/g,2*f.r/h);return et(f,g/2,h/2,i),e}var a=d3.layout.hierarchy().sort(el),b=[1,1];return c.size=function(a){return arguments.length?(b=a,c):b},ef(c,a)},d3.layout.cluster=function(){function d(d,e){var f=a.call(this,d,e),g=f[0],h,i=0,j,k;eG(g,function(a){var c=a.children;c&&c.length?(a.x=ew(c),a.y=ev(c)):(a.x=h?i+=b(a,h):0,a.y=0,h=a)});var l=ex(g),m=ey(g),n=l.x-b(l,m)/2,o=m.x+b(m,l)/2;return eG(g,function(a){a.x=(a.x-n)/(o-n)*c[0],a.y=(1-(g.y?a.y/g.y:1))*c[1]}),f}var a=d3.layout.hierarchy().sort(null).value(null),b=ez,c=[1,1];return d.separation=function(a){return arguments.length?(b=a,d):b},d.size=function(a){return arguments.length?(c=a,d):c},ef(d,a)},d3.layout.tree=function(){function d(d,e){function h(a,c){var d=a.children,e=a._tree;if(d&&(f=d.length)){var f,g=d[0],i,k=g,l,m=-1;while(++m<f)l=d[m],h(l,i),k=j(l,i,k),i=l;eH(a);var n=.5*(g._tree.prelim+l._tree.prelim);c?(e.prelim=c._tree.prelim+b(a,c),e.mod=e.prelim-n):e.prelim=n}else c&&(e.prelim=c._tree.prelim+b(a,c))}function i(a,b){a.x=a._tree.prelim+b;var c=a.children;if(c&&(e=c.length)){var d=-1,e;b+=a._tree.mod;while(++d<e)i(c[d],b)}}function j(a,c,d){if(c){var e=a,f=a,g=c,h=a.parent.children[0],i=e._tree.mod,j=f._tree.mod,k=g._tree.mod,l=h._tree.mod,m;while(g=eB(g),e=eA(e),g&&e)h=eA(h),f=eB(f),f._tree.ancestor=a,m=g._tree.prelim+k-e._tree.prelim-i+b(g,e),m>0&&(eI(eJ(g,a,d),a,m),i+=m,j+=m),k+=g._tree.mod,i+=e._tree.mod,l+=h._tree.mod,j+=f._tree.mod;g&&!eB(f)&&(f._tree.thread=g,f._tree.mod+=k-j),e&&!eA(h)&&(h._tree.thread=e,h._tree.mod+=i-l,d=a)}return d}var f=a.call(this,d,e),g=f[0];eG(g,function(a,b){a._tree={ancestor:a,prelim:0,mod:0,change:0,shift:0,number:b?b._tree.number+1:0}}),h(g),i(g,-g._tree.prelim);var k=eC(g,eE),l=eC(g,eD),m=eC(g,eF),n=k.x-b(k,l)/2,o=l.x+b(l,k)/2,p=m.depth||1;return eG(g,function(a){a.x=(a.x-n)/(o-n)*c[0],a.y=a.depth/p*c[1],delete a._tree}),f}var a=d3.layout.hierarchy().sort(null).value(null),b=ez,c=[1,1];return d.separation=function(a){return arguments.length?(b=a,d):b},d.size=function(a){return arguments.length?(c=a,d):c},ef(d,a)},d3.layout.treemap=function(){function i(a,b){var c=-1,d=a.length,e,f;while(++c<d)f=(e=a[c]).value*(b<0?0:b),e.area=isNaN(f)||f<=0?0:f}function j(a){var b=a.children;if(b&&b.length){var c=e(a),d=[],f=b.slice(),g,h=Infinity,k,n=Math.min(c.dx,c.dy),o;i(f,c.dx*c.dy/a.value),d.area=0;while((o=f.length)>0)d.push(g=f[o-1]),d.area+=g.area,(k=l(d,n))<=h?(f.pop(),h=k):(d.area-=d.pop().area,m(d,n,c,!1),n=Math.min(c.dx,c.dy),d.length=d.area=0,h=Infinity);d.length&&(m(d,n,c,!0),d.length=d.area=0),b.forEach(j)}}function k(a){var b=a.children;if(b&&b.length){var c=e(a),d=b.slice(),f,g=[];i(d,c.dx*c.dy/a.value),g.area=0;while(f=d.pop())g.push(f),g.area+=f.area,f.z!=null&&(m(g,f.z?c.dx:c.dy,c,!d.length),g.length=g.area=0);b.forEach(k)}}function l(a,b){var c=a.area,d,e=0,f=Infinity,g=-1,i=a.length;while(++g<i){if(!(d=a[g].area))continue;d<f&&(f=d),d>e&&(e=d)}return c*=c,b*=b,c?Math.max(b*e*h/c,c/(b*f*h)):Infinity}function m(a,c,d,e){var f=-1,g=a.length,h=d.x,i=d.y,j=c?b(a.area/c):0,k;if(c==d.dx){if(e||j>d.dy)j=d.dy;while(++f<g)k=a[f],k.x=h,k.y=i,k.dy=j,h+=k.dx=Math.min(d.x+d.dx-h,j?b(k.area/j):0);k.z=!0,k.dx+=d.x+d.dx-h,d.y+=j,d.dy-=j}else{if(e||j>d.dx)j=d.dx;while(++f<g)k=a[f],k.x=h,k.y=i,k.dx=j,i+=k.dy=Math.min(d.y+d.dy-i,j?b(k.area/j):0);k.z=!1,k.dy+=d.y+d.dy-i,d.x+=j,d.dx-=j}}function n(b){var d=g||a(b),e=d[0];return e.x=0,e.y=0,e.dx=c[0],e.dy=c[1],g&&a.revalue(e),i([e],e.dx*e.dy/e.value),(g?k:j)(e),f&&(g=d),d}var a=d3.layout.hierarchy(),b=Math.round,c=[1,1],d=null,e=eK,f=!1,g,h=.5*(1+Math.sqrt(5));return n.size=function(a){return arguments.length?(c=a,n):c},n.padding=function(a){function b(b){var c=a.call(n,b,b.depth);return c==null?eK(b):eL(b,typeof c=="number"?[c,c,c,c]:c)}function c(b){return eL(b,a)}if(!arguments.length)return d;var f;return e=(d=a)==null?eK:(f=typeof a)==="function"?b:f==="number"?(a=[a,a,a,a],c):c,n},n.round=function(a){return arguments.length?(b=a?Math.round:Number,n):b!=Number},n.sticky=function(a){return arguments.length?(f=a,g=null,n):f},n.ratio=function(a){return arguments.length?(h=a,n):h},ef(n,a)},d3.csv=function(a,b){d3.text(a,"text/csv",function(a){b(a&&d3.csv.parse(a))})},d3.csv.parse=function(a){var b;return d3.csv.parseRows(a,function(a,c){if(c){var d={},e=-1,f=b.length;while(++e<f)d[b[e]]=a[e];return d}return b=a,null})},d3.csv.parseRows=function(a,b){function j(){if(f.lastIndex>=a.length)return d;if(i)return i=!1,c;var b=f.lastIndex;if(a.charCodeAt(b)===34){var e=b;while(e++<a.length)if(a.charCodeAt(e)===34){if(a.charCodeAt(e+1)!==34)break;e++}f.lastIndex=e+2;var g=a.charCodeAt(e+1);return g===13?(i=!0,a.charCodeAt(e+2)===10&&f.lastIndex++):g===10&&(i=!0),a.substring(b+1,e).replace(/""/g,'"')}var h=f.exec(a);return h?(i=h[0].charCodeAt(0)!==44,a.substring(b,h.index)):(f.lastIndex=a.length,a.substring(b))}var c={},d={},e=[],f=/\r\n|[,\r\n]/g,g=0,h,i;f.lastIndex=0;while((h=j())!==d){var k=[];while(h!==c&&h!==d)k.push(h),h=j();if(b&&!(k=b(k,g++)))continue;e.push(k)}return e},d3.csv.format=function(a){return a.map(eM).join("\n")},d3.geo={};var eO=Math.PI/180;d3.geo.azimuthal=function(){function i(b){var f=b[0]*eO-e,i=b[1]*eO,j=Math.cos(f),k=Math.sin(f),l=Math.cos(i),m=Math.sin(i),n=a!=="orthographic"?h*m+g*l*j:null,o,p=a==="stereographic"?1/(1+n):a==="gnomonic"?1/n:a==="equidistant"?(o=Math.acos(n),o?o/Math.sin(o):0):a==="equalarea"?Math.sqrt(2/(1+n)):1,q=p*l*k,r=p*(h*l*j-g*m);return[c*q+d[0],c*r+d[1]]}var a="orthographic",b,c=200,d=[480,250],e,f,g,h;return i.invert=function(b){var f=(b[0]-d[0])/c,i=(b[1]-d[1])/c,j=Math.sqrt(f*f+i*i),k=a==="stereographic"?2*Math.atan(j):a==="gnomonic"?Math.atan(j):a==="equidistant"?j:a==="equalarea"?2*Math.asin(.5*j):Math.asin(j),l=Math.sin(k),m=Math.cos(k);return[(e+Math.atan2(f*l,j*g*m+i*h*l))/eO,Math.asin(m*h-(j?i*l*g/j:0))/eO]},i.mode=function(b){return arguments.length?(a=b+"",i):a},i.origin=function(a){return arguments.length?(b=a,e=b[0]*eO,f=b[1]*eO,g=Math.cos(f),h=Math.sin(f),i):b},i.scale=function(a){return arguments.length?(c=+a,i):c},i.translate=function(a){return arguments.length?(d=[+a[0],+a[1]],i):d},i.origin([0,0])},d3.geo.albers=function(){function i(a){var b=f*(eO*a[0]-e),i=Math.sqrt(g-2*f*Math.sin(eO*a[1]))/f;return[c*i*Math.sin(b)+d[0],c*(i*Math.cos(b)-h)+d[1]]}function j(){var c=eO*b[0],d=eO*b[1],j=eO*a[1],k=Math.sin(c),l=Math.cos(c);return e=eO*a[0],f=.5*(k+Math.sin(d)),g=l*l+2*f*k,h=Math.sqrt(g-2*f*Math.sin(j))/f,i}var a=[-98,38],b=[29.5,45.5],c=1e3,d=[480,250],e,f,g,h;return i.invert=function(a){var b=(a[0]-d[0])/c,i=(a[1]-d[1])/c,j=h+i,k=Math.atan2(b,j),l=Math.sqrt(b*b+j*j);return[(e+k/f)/eO,Math.asin((g-l*l*f*f)/(2*f))/eO]},i.origin=function(b){return arguments.length?(a=[+b[0],+b[1]],j()):a},i.parallels=function(a){return arguments.length?(b=[+a[0],+a[1]],j()):b},i.scale=function(a){return arguments.length?(c=+a,i):c},i.translate=function(a){return arguments.length?(d=[+a[0],+a[1]],i):d},j()},d3.geo.albersUsa=function(){function e(e){var f=e[0],g=e[1];return(g>50?b:f<-140?c:g<21?d:a)(e)}var a=d3.geo.albers(),b=d3.geo.albers().origin([-160,60]).parallels([55,65]),c=d3.geo.albers().origin([-160,20]).parallels([8,18]),d=d3.geo.albers().origin([-60,10]).parallels([8,18]);return e.scale=function(f){return arguments.length?(a.scale(f),b.scale(f*.6),c.scale(f),d.scale(f*1.5),e.translate(a.translate())):a.scale()},e.translate=function(f){if(!arguments.length)return a.translate();var g=a.scale()/1e3,h=f[0],i=f[1];return a.translate(f),b.translate([h-400*g,i+170*g]),c.translate([h-190*g,i+200*g]),d.translate([h+580*g,i+430*g]),e},e.scale(a.scale())},d3.geo.bonne=function(){function g(g){var h=g[0]*eO-c,i=g[1]*eO-d;if(e){var j=f+e-i,k=h*Math.cos(i)/j;h=j*Math.sin(k),i=j*Math.cos(k)-f}else h*=Math.cos(i),i*=-1;return[a*h+b[0],a*i+b[1]]}var a=200,b=[480,250],c,d,e,f;return g.invert=function(d){var g=(d[0]-b[0])/a,h=(d[1]-b[1])/a;if(e){var i=f+h,j=Math.sqrt(g*g+i*i);h=f+e-j,g=c+j*Math.atan2(g,i)/Math.cos(h)}else h*=-1,g/=Math.cos(h);return[g/eO,h/eO]},g.parallel=function(a){return arguments.length?(f=1/Math.tan(e=a*eO),g):e/eO},g.origin=function(a){return arguments.length?(c=a[0]*eO,d=a[1]*eO,g):[c/eO,d/eO]},g.scale=function(b){return arguments.length?(a=+b,g):a},g.translate=function(a){return arguments.length?(b=[+a[0],+a[1]],g):b},g.origin([0,0]).parallel(45)},d3.geo.equirectangular=function(){function c(c){var d=c[0]/360,e=-c[1]/360;return[a*d+b[0],a*e+b[1]]}var a=500,b=[480,250];return c.invert=function(c){var d=(c[0]-b[0])/a,e=(c[1]-b[1])/a;return[360*d,-360*e]},c.scale=function(b){return arguments.length?(a=+b,c):a},c.translate=function(a){return arguments.length?(b=[+a[0],+a[1]],c):b},c},d3.geo.mercator=function(){function c(c){var d=c[0]/360,e=-(Math.log(Math.tan(Math.PI/4+c[1]*eO/2))/eO)/360;return[a*d+b[0],a*Math.max(-0.5,Math.min(.5,e))+b[1]]}var a=500,b=[480,250];return c.invert=function(c){var d=(c[0]-b[0])/a,e=(c[1]-b[1])/a;return[360*d,2*Math.atan(Math.exp(-360*e*eO))/eO-90]},c.scale=function(b){return arguments.length?(a=+b,c):a},c.translate=function(a){return arguments.length?(b=[+a[0],+a[1]],c):b},c},d3.geo.path=function(){function d(c,d){return typeof a=="function"&&(b=eQ(a.apply(this,arguments))),f(c)||null}function e(a){return c(a).join(",")}function h(a){var b=k(a[0]),c=0,d=a.length;while(++c<d)b-=k(a[c]);return b}function i(a){var b=d3.geom.polygon(a[0].map(c)),d=b.area(),e=b.centroid(d<0?(d*=-1,1):-1),f=e[0],g=e[1],h=d,i=0,j=a.length;while(++i<j)b=d3.geom.polygon(a[i].map(c)),d=b.area(),e=b.centroid(d<0?(d*=-1,1):-1),f-=e[0],g-=e[1],h-=d;return[f,g,6*h]}function k(a){return Math.abs(d3.geom.polygon(a.map(c)).area())}var a=4.5,b=eQ(a),c=d3.geo.albersUsa(),f=eP({FeatureCollection:function(a){var b=[],c=a.features,d=-1,e=c.length;while(++d<e)b.push(f(c[d].geometry));return b.join("")},Feature:function(a){return f(a.geometry)},Point:function(a){return"M"+e(a.coordinates)+b},MultiPoint:function(a){var c=[],d=a.coordinates,f=-1,g=d.length;while(++f<g)c.push("M",e(d[f]),b);return c.join("")},LineString:function(a){var b=["M"],c=a.coordinates,d=-1,f=c.length;while(++d<f)b.push(e(c[d]),"L");return b.pop(),b.join("")},MultiLineString:function(a){var b=[],c=a.coordinates,d=-1,f=c.length,g,h,i;while(++d<f){g=c[d],h=-1,i=g.length,b.push("M");while(++h<i)b.push(e(g[h]),"L");b.pop()}return b.join("")},Polygon:function(a){var b=[],c=a.coordinates,d=-1,f=c.length,g,h,i;while(++d<f){g=c[d],h=-1;if((i=g.length-1)>0){b.push("M");while(++h<i)b.push(e(g[h]),"L");b[b.length-1]="Z"}}return b.join("")},MultiPolygon:function(a){var b=[],c=a.coordinates,d=-1,f=c.length,g,h,i,j,k,l;while(++d<f){g=c[d],h=-1,i=g.length;while(++h<i){j=g[h],k=-1;if((l=j.length-1)>0){b.push("M");while(++k<l)b.push(e(j[k]),"L");b[b.length-1]="Z"}}}return b.join("")},GeometryCollection:function(a){var b=[],c=a.geometries,d=-1,e=c.length;while(++d<e)b.push(f(c[d]));return b.join("")}}),g=d.area=eP({FeatureCollection:function(a){var b=0,c=a.features,d=-1,e=c.length;while(++d<e)b+=g(c[d]);return b},Feature:function(a){return g(a.geometry)},Polygon:function(a){return h(a.coordinates)},MultiPolygon:function(a){var b=0,c=a.coordinates,d=-1,e=c.length;while(++d<e)b+=h(c[d]);return b},GeometryCollection:function(a){var b=0,c=a.geometries,d=-1,e=c.length;while(++d<e)b+=g(c[d]);return b}},0),j=d.centroid=eP({Feature:function(a){return j(a.geometry)},Polygon:function(a){var b=i(a.coordinates);return[b[0]/b[2],b[1]/b[2]]},MultiPolygon:function(a){var b=0,c=a.coordinates,d,e=0,f=0,g=0,h=-1,j=c.length;while(++h<j)d=i(c[h]),e+=d[0],f+=d[1],g+=d[2];return[e/g,f/g]}});return d.projection=function(a){return c=a,d},d.pointRadius=function(c){return typeof c=="function"?a=c:(a=+c,b=eQ(a)),d},d},d3.geo.bounds=function(a){var b=Infinity,c=Infinity,d=-Infinity,e=-Infinity;return eR(a,function(a,f){a<b&&(b=a),a>d&&(d=a),f<c&&(c=f),f>e&&(e=f)}),[[b,c],[d,e]]};var eS={Feature:eT,FeatureCollection:eU,GeometryCollection:eV,LineString:eW,MultiLineString:eX,MultiPoint:eW,MultiPolygon:eY,Point:eZ,Polygon:e$};d3.geo.circle=function(){function e(){}function f(a){return d.distance(a)<c}function h(a){var b=-1,e=a.length,f=[],g,h,j,k,l;while(++b<e)l=d.distance(j=a[b]),l<c?(h&&f.push(fb(h,j)((k-c)/(k-l))),f.push(j),g=h=null):(h=j,!g&&f.length&&(f.push(fb(f[f.length-1],h)((c-k)/(l-k))),g=h)),k=l;return h&&f.length&&(l=d.distance(j=f[0]),f.push(fb(h,j)((k-c)/(k-l)))),i(f)}function i(a){var b=0,c=a.length,e,f,g=c?[a[0]]:a,h,i=d.source();while(++b<c){h=d.source(a[b-1])(a[b]).coordinates;for(e=0,f=h.length;++e<f;)g.push(h[e])}return d.source(i),g}var a=[0,0],b=89.99,c=b*eO,d=d3.geo.greatArc().target(Object);e.clip=function(b){return d.source(typeof a=="function"?a.apply(this,arguments):a),g(b)};var g=eP({FeatureCollection:function(a){var b=a.features.map(g).filter(Object);return b&&(a=Object.create(a),a.features=b,a)},Feature:function(a){var b=g(a.geometry);return b&&(a=Object.create(a),a.geometry=b,a)},Point:function(a){return f
(a.coordinates)&&a},MultiPoint:function(a){var b=a.coordinates.filter(f);return b.length&&{type:a.type,coordinates:b}},LineString:function(a){var b=h(a.coordinates);return b.length&&(a=Object.create(a),a.coordinates=b,a)},MultiLineString:function(a){var b=a.coordinates.map(h).filter(function(a){return a.length});return b.length&&(a=Object.create(a),a.coordinates=b,a)},Polygon:function(a){var b=a.coordinates.map(h);return b[0].length&&(a=Object.create(a),a.coordinates=b,a)},MultiPolygon:function(a){var b=a.coordinates.map(function(a){return a.map(h)}).filter(function(a){return a[0].length});return b.length&&(a=Object.create(a),a.coordinates=b,a)},GeometryCollection:function(a){var b=a.geometries.map(g).filter(Object);return b.length&&(a=Object.create(a),a.geometries=b,a)}});return e.origin=function(b){return arguments.length?(a=b,e):a},e.angle=function(a){return arguments.length?(c=(b=+a)*eO,e):b},e.precision=function(a){return arguments.length?(d.precision(a),e):d.precision()},e},d3.geo.greatArc=function(){function d(){var d=typeof a=="function"?a.apply(this,arguments):a,e=typeof b=="function"?b.apply(this,arguments):b,f=fb(d,e),g=c/f.d,h=0,i=[d];while((h+=g)<1)i.push(f(h));return i.push(e),{type:"LineString",coordinates:i}}var a=e_,b=fa,c=6*eO;return d.distance=function(){var c=typeof a=="function"?a.apply(this,arguments):a,d=typeof b=="function"?b.apply(this,arguments):b;return fb(c,d).d},d.source=function(b){return arguments.length?(a=b,d):a},d.target=function(a){return arguments.length?(b=a,d):b},d.precision=function(a){return arguments.length?(c=a*eO,d):c/eO},d},d3.geo.greatCircle=d3.geo.circle,d3.geom={},d3.geom.contour=function(a,b){var c=b||fe(a),d=[],e=c[0],f=c[1],g=0,h=0,i=NaN,j=NaN,k=0;do k=0,a(e-1,f-1)&&(k+=1),a(e,f-1)&&(k+=2),a(e-1,f)&&(k+=4),a(e,f)&&(k+=8),k===6?(g=j===-1?-1:1,h=0):k===9?(g=0,h=i===1?-1:1):(g=fc[k],h=fd[k]),g!=i&&h!=j&&(d.push([e,f]),i=g,j=h),e+=g,f+=h;while(c[0]!=e||c[1]!=f);return d};var fc=[1,0,1,1,-1,0,-1,1,0,0,0,0,-1,0,-1,NaN],fd=[0,-1,0,0,0,-1,0,0,1,-1,1,1,0,-1,0,NaN];d3.geom.hull=function(a){if(a.length<3)return[];var b=a.length,c=b-1,d=[],e=[],f,g,h=0,i,j,k,l,m,n,o,p;for(f=1;f<b;++f)a[f][1]<a[h][1]?h=f:a[f][1]==a[h][1]&&(h=a[f][0]<a[h][0]?f:h);for(f=0;f<b;++f){if(f===h)continue;j=a[f][1]-a[h][1],i=a[f][0]-a[h][0],d.push({angle:Math.atan2(j,i),index:f})}d.sort(function(a,b){return a.angle-b.angle}),o=d[0].angle,n=d[0].index,m=0;for(f=1;f<c;++f)g=d[f].index,o==d[f].angle?(i=a[n][0]-a[h][0],j=a[n][1]-a[h][1],k=a[g][0]-a[h][0],l=a[g][1]-a[h][1],i*i+j*j>=k*k+l*l?d[f].index=-1:(d[m].index=-1,o=d[f].angle,m=f,n=g)):(o=d[f].angle,m=f,n=g);e.push(h);for(f=0,g=0;f<2;++g)d[g].index!==-1&&(e.push(d[g].index),f++);p=e.length;for(;g<c;++g){if(d[g].index===-1)continue;while(!ff(e[p-2],e[p-1],d[g].index,a))--p;e[p++]=d[g].index}var q=[];for(f=0;f<p;++f)q.push(a[e[f]]);return q},d3.geom.polygon=function(a){return a.area=function(){var b=0,c=a.length,d=a[c-1][0]*a[0][1],e=a[c-1][1]*a[0][0];while(++b<c)d+=a[b-1][0]*a[b][1],e+=a[b-1][1]*a[b][0];return(e-d)*.5},a.centroid=function(b){var c=-1,d=a.length,e=0,f=0,g,h=a[d-1],i;arguments.length||(b=-1/(6*a.area()));while(++c<d)g=h,h=a[c],i=g[0]*h[1]-h[0]*g[1],e+=(g[0]+h[0])*i,f+=(g[1]+h[1])*i;return[e*b,f*b]},a.clip=function(b){var c,d=-1,e=a.length,f,g,h=a[e-1],i,j,k;while(++d<e){c=b.slice(),b.length=0,i=a[d],j=c[(g=c.length)-1],f=-1;while(++f<g)k=c[f],fg(k,h,i)?(fg(j,h,i)||b.push(fh(j,k,h,i)),b.push(k)):fg(j,h,i)&&b.push(fh(j,k,h,i)),j=k;h=i}return b},a},d3.geom.voronoi=function(a){var b=a.map(function(){return[]});return fj(a,function(a){var c,d,e,f,g,h;a.a===1&&a.b>=0?(c=a.ep.r,d=a.ep.l):(c=a.ep.l,d=a.ep.r),a.a===1?(g=c?c.y:-1e6,e=a.c-a.b*g,h=d?d.y:1e6,f=a.c-a.b*h):(e=c?c.x:-1e6,g=a.c-a.a*e,f=d?d.x:1e6,h=a.c-a.a*f);var i=[e,g],j=[f,h];b[a.region.l.index].push(i,j),b[a.region.r.index].push(i,j)}),b.map(function(b,c){var d=a[c][0],e=a[c][1];return b.forEach(function(a){a.angle=Math.atan2(a[0]-d,a[1]-e)}),b.sort(function(a,b){return a.angle-b.angle}).filter(function(a,c){return!c||a.angle-b[c-1].angle>1e-10})})};var fi={l:"r",r:"l"};d3.geom.delaunay=function(a){var b=a.map(function(){return[]}),c=[];return fj(a,function(c){b[c.region.l.index].push(a[c.region.r.index])}),b.forEach(function(b,d){var e=a[d],f=e[0],g=e[1];b.forEach(function(a){a.angle=Math.atan2(a[0]-f,a[1]-g)}),b.sort(function(a,b){return a.angle-b.angle});for(var h=0,i=b.length-1;h<i;h++)c.push([e,b[h],b[h+1]])}),c},d3.geom.quadtree=function(a,b,c,d,e){function k(a,b,c,d,e,f){if(isNaN(b.x)||isNaN(b.y))return;if(a.leaf){var g=a.point;g?Math.abs(g.x-b.x)+Math.abs(g.y-b.y)<.01?l(a,b,c,d,e,f):(a.point=null,l(a,g,c,d,e,f),l(a,b,c,d,e,f)):a.point=b}else l(a,b,c,d,e,f)}function l(a,b,c,d,e,f){var g=(c+e)*.5,h=(d+f)*.5,i=b.x>=g,j=b.y>=h,l=(j<<1)+i;a.leaf=!1,a=a.nodes[l]||(a.nodes[l]=fk()),i?c=g:e=g,j?d=h:f=h,k(a,b,c,d,e,f)}var f,g=-1,h=a.length;h&&isNaN(a[0].x)&&(a=a.map(fm));if(arguments.length<5)if(arguments.length===3)e=d=c,c=b;else{b=c=Infinity,d=e=-Infinity;while(++g<h)f=a[g],f.x<b&&(b=f.x),f.y<c&&(c=f.y),f.x>d&&(d=f.x),f.y>e&&(e=f.y);var i=d-b,j=e-c;i>j?e=c+i:d=b+j}var m=fk();return m.add=function(a){k(m,a,b,c,d,e)},m.visit=function(a){fl(a,m,b,c,d,e)},a.forEach(m.add),m},d3.time={};var fn=Date;fo.prototype={getDate:function(){return this._.getUTCDate()},getDay:function(){return this._.getUTCDay()},getFullYear:function(){return this._.getUTCFullYear()},getHours:function(){return this._.getUTCHours()},getMilliseconds:function(){return this._.getUTCMilliseconds()},getMinutes:function(){return this._.getUTCMinutes()},getMonth:function(){return this._.getUTCMonth()},getSeconds:function(){return this._.getUTCSeconds()},getTime:function(){return this._.getTime()},getTimezoneOffset:function(){return 0},valueOf:function(){return this._.valueOf()},setDate:function(){fp.setUTCDate.apply(this._,arguments)},setDay:function(){fp.setUTCDay.apply(this._,arguments)},setFullYear:function(){fp.setUTCFullYear.apply(this._,arguments)},setHours:function(){fp.setUTCHours.apply(this._,arguments)},setMilliseconds:function(){fp.setUTCMilliseconds.apply(this._,arguments)},setMinutes:function(){fp.setUTCMinutes.apply(this._,arguments)},setMonth:function(){fp.setUTCMonth.apply(this._,arguments)},setSeconds:function(){fp.setUTCSeconds.apply(this._,arguments)},setTime:function(){fp.setTime.apply(this._,arguments)}};var fp=Date.prototype;d3.time.format=function(a){function c(c){var d=[],e=-1,f=0,g,h;while(++e<b)a.charCodeAt(e)==37&&(d.push(a.substring(f,e),(h=fv[g=a.charAt(++e)])?h(c):g),f=e+1);return d.push(a.substring(f,e)),d.join("")}var b=a.length;return c.parse=function(b){var c={y:1900,m:0,d:1,H:0,M:0,S:0,L:0},d=fq(c,a,b,0);if(d!=b.length)return null;"p"in c&&(c.H=c.H%12+c.p*12);var e=new fn;return e.setFullYear(c.y,c.m,c.d),e.setHours(c.H,c.M,c.S,c.L),e},c.toString=function(){return a},c};var fr=d3.format("02d"),fs=d3.format("03d"),ft=d3.format("04d"),fu=d3.format("2d"),fv={a:function(a){return d3_time_weekdays[a.getDay()].substring(0,3)},A:function(a){return d3_time_weekdays[a.getDay()]},b:function(a){return fG[a.getMonth()].substring(0,3)},B:function(a){return fG[a.getMonth()]},c:d3.time.format("%a %b %e %H:%M:%S %Y"),d:function(a){return fr(a.getDate())},e:function(a){return fu(a.getDate())},H:function(a){return fr(a.getHours())},I:function(a){return fr(a.getHours()%12||12)},j:function(a){return fs(1+d3.time.dayOfYear(a))},L:function(a){return fs(a.getMilliseconds())},m:function(a){return fr(a.getMonth()+1)},M:function(a){return fr(a.getMinutes())},p:function(a){return a.getHours()>=12?"PM":"AM"},S:function(a){return fr(a.getSeconds())},U:function(a){return fr(d3.time.sundayOfYear(a))},w:function(a){return a.getDay()},W:function(a){return fr(d3.time.mondayOfYear(a))},x:d3.time.format("%m/%d/%y"),X:d3.time.format("%H:%M:%S"),y:function(a){return fr(a.getFullYear()%100)},Y:function(a){return ft(a.getFullYear()%1e4)},Z:fW,"%":function(a){return"%"}},fw={a:fx,A:fy,b:fB,B:fD,c:fH,d:fO,e:fO,H:fP,I:fP,L:fS,m:fN,M:fQ,p:fU,S:fR,x:fI,X:fJ,y:fL,Y:fK},fz=/^(?:sun|mon|tue|wed|thu|fri|sat)/i,fA=/^(?:Sunday|Monday|Tuesday|Wednesday|Thursday|Friday|Saturday)/i;d3_time_weekdays=["Sunday","Monday","Tuesday","Wednesday","Thursday","Friday","Saturday"];var fC=d3.map({jan:0,feb:1,mar:2,apr:3,may:4,jun:5,jul:6,aug:7,sep:8,oct:9,nov:10,dec:11}),fE=/^(?:January|February|March|April|May|June|July|August|September|October|November|December)/ig,fF=d3.map({january:0,february:1,march:2,april:3,may:4,june:5,july:6,august:7,september:8,october:9,november:10,december:11}),fG=["January","February","March","April","May","June","July","August","September","October","November","December"],fT=/\s*\d+/,fV=d3.map({am:0,pm:1});d3.time.format.utc=function(a){function c(a){try{fn=fo;var c=new fn;return c._=a,b(c)}finally{fn=Date}}var b=d3.time.format(a);return c.parse=function(a){try{fn=fo;var c=b.parse(a);return c&&c._}finally{fn=Date}},c.toString=b.toString,c};var fX=d3.time.format.utc("%Y-%m-%dT%H:%M:%S.%LZ");d3.time.format.iso=Date.prototype.toISOString?fY:fX,fY.parse=function(a){return new Date(a)},fY.toString=fX.toString,d3.time.second=fZ(function(a){return new fn(Math.floor(a/1e3)*1e3)},function(a,b){a.setTime(a.getTime()+Math.floor(b)*1e3)},function(a){return a.getSeconds()}),d3.time.seconds=d3.time.second.range,d3.time.seconds.utc=d3.time.second.utc.range,d3.time.minute=fZ(function(a){return new fn(Math.floor(a/6e4)*6e4)},function(a,b){a.setTime(a.getTime()+Math.floor(b)*6e4)},function(a){return a.getMinutes()}),d3.time.minutes=d3.time.minute.range,d3.time.minutes.utc=d3.time.minute.utc.range,d3.time.hour=fZ(function(a){var b=a.getTimezoneOffset()/60;return new fn((Math.floor(a/36e5-b)+b)*36e5)},function(a,b){a.setTime(a.getTime()+Math.floor(b)*36e5)},function(a){return a.getHours()}),d3.time.hours=d3.time.hour.range,d3.time.hours.utc=d3.time.hour.utc.range,d3.time.day=fZ(function(a){return new fn(a.getFullYear(),a.getMonth(),a.getDate())},function(a,b){a.setDate(a.getDate()+b)},function(a){return a.getDate()-1}),d3.time.days=d3.time.day.range,d3.time.days.utc=d3.time.day.utc.range,d3.time.dayOfYear=function(a){var b=d3.time.year(a);return Math.floor((a-b)/864e5-(a.getTimezoneOffset()-b.getTimezoneOffset())/1440)},d3_time_weekdays.forEach(function(a,b){a=a.toLowerCase(),b=7-b;var c=d3.time[a]=fZ(function(a){return(a=d3.time.day(a)).setDate(a.getDate()-(a.getDay()+b)%7),a},function(a,b){a.setDate(a.getDate()+Math.floor(b)*7)},function(a){var c=d3.time.year(a).getDay();return Math.floor((d3.time.dayOfYear(a)+(c+b)%7)/7)-(c!==b)});d3.time[a+"s"]=c.range,d3.time[a+"s"].utc=c.utc.range,d3.time[a+"OfYear"]=function(a){var c=d3.time.year(a).getDay();return Math.floor((d3.time.dayOfYear(a)+(c+b)%7)/7)}}),d3.time.week=d3.time.sunday,d3.time.weeks=d3.time.sunday.range,d3.time.weeks.utc=d3.time.sunday.utc.range,d3.time.weekOfYear=d3.time.sundayOfYear,d3.time.month=fZ(function(a){return new fn(a.getFullYear(),a.getMonth(),1)},function(a,b){a.setMonth(a.getMonth()+b)},function(a){return a.getMonth()}),d3.time.months=d3.time.month.range,d3.time.months.utc=d3.time.month.utc.range,d3.time.year=fZ(function(a){return new fn(a.getFullYear(),0,1)},function(a,b){a.setFullYear(a.getFullYear()+b)},function(a){return a.getFullYear()}),d3.time.years=d3.time.year.range,d3.time.years.utc=d3.time.year.utc.range;var gf=[1e3,5e3,15e3,3e4,6e4,3e5,9e5,18e5,36e5,108e5,216e5,432e5,864e5,1728e5,6048e5,2592e6,7776e6,31536e6],gg=[[d3.time.second,1],[d3.time.second,5],[d3.time.second,15],[d3.time.second,30],[d3.time.minute,1],[d3.time.minute,5],[d3.time.minute,15],[d3.time.minute,30],[d3.time.hour,1],[d3.time.hour,3],[d3.time.hour,6],[d3.time.hour,12],[d3.time.day,1],[d3.time.day,2],[d3.time.week,1],[d3.time.month,1],[d3.time.month,3],[d3.time.year,1]],gh=[[d3.time.format("%Y"),function(a){return!0}],[d3.time.format("%B"),function(a){return a.getMonth()}],[d3.time.format("%b %d"),function(a){return a.getDate()!=1}],[d3.time.format("%a %d"),function(a){return a.getDay()&&a.getDate()!=1}],[d3.time.format("%I %p"),function(a){return a.getHours()}],[d3.time.format("%I:%M"),function(a){return a.getMinutes()}],[d3.time.format(":%S"),function(a){return a.getSeconds()}],[d3.time.format(".%L"),function(a){return a.getMilliseconds()}]],gi=d3.scale.linear(),gj=gc(gh);gg.year=function(a,b){return gi.domain(a.map(ge)).ticks(b).map(gd)},d3.time.scale=function(){return f_(d3.scale.linear(),gg,gj)};var gk=gg.map(function(a){return[a[0].utc,a[1]]}),gl=[[d3.time.format.utc("%Y"),function(a){return!0}],[d3.time.format.utc("%B"),function(a){return a.getUTCMonth()}],[d3.time.format.utc("%b %d"),function(a){return a.getUTCDate()!=1}],[d3.time.format.utc("%a %d"),function(a){return a.getUTCDay()&&a.getUTCDate()!=1}],[d3.time.format.utc("%I %p"),function(a){return a.getUTCHours()}],[d3.time.format.utc("%I:%M"),function(a){return a.getUTCMinutes()}],[d3.time.format.utc(":%S"),function(a){return a.getUTCSeconds()}],[d3.time.format.utc(".%L"),function(a){return a.getUTCMilliseconds()}]],gm=gc(gl);gk.year=function(a,b){return gi.domain(a.map(go)).ticks(b).map(gn)},d3.time.scale.utc=function(){return f_(d3.scale.linear(),gk,gm)}})();
/*
 Highcharts JS v2.1.2 (2011-01-12)

 (c) 2009-2010 Torstein H?nsi

 License: www.highcharts.com/license
*/
(function(){function ma(a,b){a||(a={});for(var c in b)a[c]=b[c];return a}function oa(a,b){return parseInt(a,b||10)}function Ib(a){return typeof a=="string"}function Jb(a){return typeof a=="object"}function bc(a){return typeof a=="number"}function mc(a,b){for(var c=a.length;c--;)if(a[c]==b){a.splice(c,1);break}}function L(a){return a!==Qa&&a!==null}function xa(a,b,c){var d,e;if(Ib(b))if(L(c))a.setAttribute(b,c);else{if(a&&a.getAttribute)e=a.getAttribute(b)}else if(L(b)&&Jb(b))for(d in b)a.setAttribute(d,
b[d]);return e}function nc(a){if(!a||a.constructor!=Array)a=[a];return a}function y(){var a=arguments,b,c,d=a.length;for(b=0;b<d;b++){c=a[b];if(typeof c!=="undefined"&&c!==null)return c}}function Vd(a){var b="",c;for(c in a)b+=Ad(c)+":"+a[c]+";";return b}function La(a,b){if(Ac)if(b&&b.opacity!==Qa)b.filter="alpha(opacity="+b.opacity*100+")";ma(a.style,b)}function eb(a,b,c,d,e){a=za.createElement(a);b&&ma(a,b);e&&La(a,{padding:0,border:mb,margin:0});c&&La(a,c);d&&d.appendChild(a);return a}function Kb(a,
b){Bc=y(a,b.animation)}function Bd(){var a=Ra.global.useUTC;Cc=a?Date.UTC:function(b,c,d,e,f,g){return(new Date(b,c,y(d,1),y(e,0),y(f,0),y(g,0))).getTime()};$c=a?"getUTCMinutes":"getMinutes";ad=a?"getUTCHours":"getHours";bd=a?"getUTCDay":"getDay";oc=a?"getUTCDate":"getDate";Dc=a?"getUTCMonth":"getMonth";Ec=a?"getUTCFullYear":"getFullYear";Cd=a?"setUTCMinutes":"setMinutes";Dd=a?"setUTCHours":"setHours";cd=a?"setUTCDate":"setDate";Ed=a?"setUTCMonth":"setMonth";Fd=a?"setUTCFullYear":"setFullYear"}function Fc(a){Gc||
(Gc=eb(Lb));a&&Gc.appendChild(a);Gc.innerHTML=""}function wb(a,b){var c=function(){};c.prototype=new a;ma(c.prototype,b);return c}function Gd(a,b,c,d){var e=Ra.lang;a=a;var f=isNaN(b=ab(b))?2:b;b=c===undefined?e.decimalPoint:c;d=d===undefined?e.thousandsSep:d;e=a<0?"-":"";c=oa(a=ab(+a||0).toFixed(f))+"";var g=(g=c.length)>3?g%3:0;return e+(g?c.substr(0,g)+d:"")+c.substr(g).replace(/(\d{3})(?=\d)/g,"$1"+d)+(f?b+ab(a-c).toFixed(f).slice(2):"")}function Hc(){}function Hd(a,b){function c(m,h){function x(l,
p){this.pos=l;this.minor=p;this.isNew=true;p||this.addLabel()}function w(l){if(l){this.options=l;this.id=l.id}return this}function P(){var l=[],p=[],r;Sa=v=null;Y=[];t(Aa,function(o){r=false;t(["xAxis","yAxis"],function(ja){if(o.isCartesian&&(ja=="xAxis"&&ka||ja=="yAxis"&&!ka)&&(o.options[ja]==h.index||o.options[ja]===Qa&&h.index===0)){o[ja]=s;Y.push(o);r=true}});if(!o.visible&&u.ignoreHiddenSeries)r=false;if(r){var U,X,H,C,fa;if(!ka){U=o.options.stacking;Ic=U=="percent";if(U){C=o.type+y(o.options.stack,
"");fa="-"+C;o.stackKey=C;X=l[C]||[];l[C]=X;H=p[fa]||[];p[fa]=H}if(Ic){Sa=0;v=99}}if(o.isCartesian){t(o.data,function(ja){var D=ja.x,la=ja.y,S=la<0,Z=S?H:X;S=S?fa:C;if(Sa===null)Sa=v=ja[I];if(ka)if(D>v)v=D;else{if(D<Sa)Sa=D}else if(L(la)){if(U)Z[D]=L(Z[D])?Z[D]+la:la;la=Z?Z[D]:la;ja=y(ja.low,la);if(!Ic)if(la>v)v=la;else if(ja<Sa)Sa=ja;if(U){ca[S]||(ca[S]={});ca[S][D]={total:la,cum:la}}}});if(/(area|column|bar)/.test(o.type)&&!ka)if(Sa>=0){Sa=0;Id=true}else if(v<0){v=0;Jd=true}}}})}function ga(l,p){var r;
Db=p?1:Ta.pow(10,Mb(Ta.log(l)/Ta.LN10));r=l/Db;if(!p){p=[1,2,2.5,5,10];if(h.allowDecimals===false)if(Db==1)p=[1,2,5,10];else if(Db<=0.1)p=[1/Db]}for(var o=0;o<p.length;o++){l=p[o];if(r<=(p[o]+(p[o+1]||p[o]))/2)break}l*=Db;return l}function M(l){var p;p=l;if(L(Db)){p=(Db<1?V(1/Db):1)*10;p=V(l*p)/p}return p}function da(){var l,p,r,o,U=h.tickInterval,X=h.tickPixelInterval;l=h.maxZoom||(ka?nb(m.smallestInterval*5,v-Sa):null);B=O?Ca:ra;if(Nb){r=m[ka?"xAxis":"yAxis"][h.linkedTo];o=r.getExtremes();J=y(o.min,
o.dataMin);Q=y(o.max,o.dataMax)}else{J=y(na,h.min,Sa);Q=y(Ma,h.max,v)}if(Q-J<l){o=(l-Q+J)/2;J=Ga(J-o,y(h.min,J-o),Sa);Q=nb(J+l,y(h.max,J+l),v)}if(!bb&&!Ic&&!Nb&&L(J)&&L(Q)){l=Q-J||1;if(!L(h.min)&&!L(na)&&Wb&&(Sa<0||!Id))J-=l*Wb;if(!L(h.max)&&!L(Ma)&&Kd&&(v>0||!Jd))Q+=l*Kd}Ua=J==Q?1:Nb&&!U&&X==r.options.tickPixelInterval?r.tickInterval:y(U,bb?1:(Q-J)*X/B);if(!N&&!L(h.tickInterval))Ua=ga(Ua);s.tickInterval=Ua;Jc=h.minorTickInterval==="auto"&&Ua?Ua/5:h.minorTickInterval;if(N){pa=[];U=Ra.global.useUTC;
var H=1E3/ob,C=6E4/ob,fa=36E5/ob;X=864E5/ob;l=6048E5/ob;o=2592E6/ob;var ja=31556952E3/ob,D=[["second",H,[1,2,5,10,15,30]],["minute",C,[1,2,5,10,15,30]],["hour",fa,[1,2,3,4,6,8,12]],["day",X,[1,2]],["week",l,[1,2]],["month",o,[1,2,3,4,6]],["year",ja,null]],la=D[6],S=la[1],Z=la[2];for(r=0;r<D.length;r++){la=D[r];S=la[1];Z=la[2];if(D[r+1])if(Ua<=(S*Z[Z.length-1]+D[r+1][1])/2)break}if(S==ja&&Ua<5*S)Z=[1,2,5];D=ga(Ua/S,Z);Z=new Date(J*ob);Z.setMilliseconds(0);if(S>=H)Z.setSeconds(S>=C?0:D*Mb(Z.getSeconds()/
D));if(S>=C)Z[Cd](S>=fa?0:D*Mb(Z[$c]()/D));if(S>=fa)Z[Dd](S>=X?0:D*Mb(Z[ad]()/D));if(S>=X)Z[cd](S>=o?1:D*Mb(Z[oc]()/D));if(S>=o){Z[Ed](S>=ja?0:D*Mb(Z[Dc]()/D));p=Z[Ec]()}if(S>=ja){p-=p%D;Z[Fd](p)}S==l&&Z[cd](Z[oc]()-Z[bd]()+h.startOfWeek);r=1;p=Z[Ec]();H=Z.getTime()/ob;C=Z[Dc]();for(fa=Z[oc]();H<Q&&r<Ca;){pa.push(H);if(S==ja)H=Cc(p+r*D,0)/ob;else if(S==o)H=Cc(p,C+r*D)/ob;else if(!U&&(S==X||S==l))H=Cc(p,C,fa+r*D*(S==X?1:7));else H+=S*D;r++}pa.push(H);Kc=h.dateTimeLabelFormats[la[0]]}else{r=Mb(J/Ua)*
Ua;p=dd(Q/Ua)*Ua;pa=[];for(r=M(r);r<=p;){pa.push(r);r=M(r+Ua)}}if(!Nb){if(bb||ka&&m.hasColumn){p=(bb?1:Ua)*0.5;if(bb||!L(y(h.min,na)))J-=p;if(bb||!L(y(h.max,Ma)))Q+=p}p=pa[0];r=pa[pa.length-1];if(h.startOnTick)J=p;else J>p&&pa.shift();if(h.endOnTick)Q=r;else Q<r&&pa.pop();Eb||(Eb={x:0,y:0});if(!N&&pa.length>Eb[I])Eb[I]=pa.length}}function Da(){var l,p;fb=J;cc=Q;P();da();ha=F;F=B/(Q-J||1);if(!ka)for(l in ca)for(p in ca[l])ca[l][p].cum=ca[l][p].total;if(!s.isDirty)s.isDirty=J!=fb||Q!=cc}function sa(l){l=
(new w(l)).render();Ob.push(l);return l}function Ya(){var l=h.title,p=h.alternateGridColor,r=h.lineWidth,o,U,X=m.hasRendered,H=X&&L(fb)&&!isNaN(fb);o=Y.length&&L(J)&&L(Q);B=O?Ca:ra;F=B/(Q-J||1);va=O?W:pb;if(o||Nb){if(Jc&&!bb)for(o=J+(pa[0]-J)%Jc;o<=Q;o+=Jc){Xb[o]||(Xb[o]=new x(o,true));H&&Xb[o].isNew&&Xb[o].render(null,true);Xb[o].isActive=true;Xb[o].render()}t(pa,function(C,fa){if(!Nb||C>=J&&C<=Q){H&&qb[C].isNew&&qb[C].render(fa,true);qb[C].isActive=true;qb[C].render(fa)}});p&&t(pa,function(C,fa){if(fa%
2===0&&C<Q){dc[C]||(dc[C]=new w);dc[C].options={from:C,to:pa[fa+1]!==Qa?pa[fa+1]:Q,color:p};dc[C].render();dc[C].isActive=true}});X||t((h.plotLines||[]).concat(h.plotBands||[]),function(C){Ob.push((new w(C)).render())})}t([qb,Xb,dc],function(C){for(var fa in C)if(C[fa].isActive)C[fa].isActive=false;else{C[fa].destroy();delete C[fa]}});if(r){o=W+(Na?Ca:0)+R;U=Oa-pb-(Na?ra:0)+R;o=$.crispLine([Wa,O?W:o,O?U:aa,Ba,O?Va-zb:o,O?U:Oa-pb],r);if(Ea)Ea.animate({d:o});else Ea=$.path(o).attr({stroke:h.lineColor,
"stroke-width":r,zIndex:7}).add()}if(s.axisTitle){o=O?W:aa;r=oa(l.style.fontSize||12);o={low:o+(O?0:B),middle:o+B/2,high:o+(O?B:0)}[l.align];r=(O?aa+ra:W)+(O?1:-1)*(Na?-1:1)*ed+(G==2?r:0);s.axisTitle[X?"animate":"attr"]({x:O?o:r+(Na?Ca:0)+R+(l.x||0),y:O?r-(Na?ra:0)+R:o+(l.y||0)})}s.isDirty=false}function Ha(l){for(var p=0;p<Ob.length;p++)Ob[p].id==l&&Ob[p].destroy()}var ka=h.isX,Na=h.opposite,O=Fa?!ka:ka,G=O?Na?0:2:Na?1:3,ca={};h=wa(ka?Lc:fd,[Wd,Xd,Ld,Yd][G],h);var s=this,N=h.type=="datetime",R=h.offset||
0,I=ka?"x":"y",B,F,ha,va=O?W:pb,ta,Ia,rb,Fb,Ea,Sa,v,Y,na,Ma,Q=null,J=null,fb,cc,Wb=h.minPadding,Kd=h.maxPadding,Nb=L(h.linkedTo),Id,Jd,Ic,Md=h.events,gd,Ob=[],Ua,Jc,Db,pa,qb={},Xb={},dc={},ec,fc,ed,Kc,bb=h.categories,Zd=h.labels.formatter||function(){var l=this.value;return Kc?Mc(Kc,l):Ua%1E6===0?l/1E6+"M":Ua%1E3===0?l/1E3+"k":!bb&&l>=1E3?Gd(l,0):l},Nc=O&&h.labels.staggerLines,Yb=h.reversed,Zb=bb&&h.tickmarkPlacement=="between"?0.5:0;x.prototype={addLabel:function(){var l=this.pos,p=h.labels,r=!(l==
J&&!y(h.showFirstLabel,1)||l==Q&&!y(h.showLastLabel,0)),o,U=this.label;l=Zd.call({isFirst:l==pa[0],isLast:l==pa[pa.length-1],dateTimeLabelFormat:Kc,value:bb&&bb[l]?bb[l]:l});o=o&&{width:o-2*(p.padding||10)+Za};if(U===Qa)this.label=L(l)&&r&&p.enabled?$.text(l,0,0).attr({align:p.align,rotation:p.rotation}).css(ma(o,p.style)).add(rb):null;else U&&U.attr({text:l}).css(o)},getLabelSize:function(){var l=this.label;return l?(this.labelBBox=l.getBBox())[O?"height":"width"]:0},render:function(l,p){var r=!this.minor,
o=this.label,U=this.pos,X=h.labels,H=this.gridLine,C=r?h.gridLineWidth:h.minorGridLineWidth,fa=r?h.gridLineColor:h.minorGridLineColor,ja=r?h.gridLineDashStyle:h.minorGridLineDashStyle,D=this.mark,la=r?h.tickLength:h.minorTickLength,S=r?h.tickWidth:h.minorTickWidth||0,Z=r?h.tickColor:h.minorTickColor,pc=r?h.tickPosition:h.minorTickPosition;r=X.step;var gb=p&&Oc||Oa,Pb;Pb=O?ta(U+Zb,null,null,p)+va:W+R+(Na?(p&&hd||Va)-zb-W:0);gb=O?gb-pb+R-(Na?ra:0):gb-ta(U+Zb,null,null,p)-va;if(C){U=Ia(U+Zb,C,p);if(H===
Qa){H={stroke:fa,"stroke-width":C};if(ja)H.dashstyle=ja;this.gridLine=H=C?$.path(U).attr(H).add(Fb):null}H&&U&&H.animate({d:U})}if(S){if(pc=="inside")la=-la;if(Na)la=-la;C=$.crispLine([Wa,Pb,gb,Ba,Pb+(O?0:-la),gb+(O?la:0)],S);if(D)D.animate({d:C});else this.mark=$.path(C).attr({stroke:Z,"stroke-width":S}).add(rb)}if(o){Pb=Pb+X.x-(Zb&&O?Zb*F*(Yb?-1:1):0);gb=gb+X.y-(Zb&&!O?Zb*F*(Yb?1:-1):0);L(X.y)||(gb+=parseInt(o.styles.lineHeight)*0.9-o.getBBox().height/2);if(Nc)gb+=l%Nc*16;if(r)o[l%r?"hide":"show"]();
o[this.isNew?"attr":"animate"]({x:Pb,y:gb})}this.isNew=false},destroy:function(){for(var l in this)this[l]&&this[l].destroy&&this[l].destroy()}};w.prototype={render:function(){var l=this,p=l.options,r=p.label,o=l.label,U=p.width,X=p.to,H,C=p.from,fa=p.dashStyle,ja=l.svgElem,D=[],la,S,Z=p.color;S=p.zIndex;var pc=p.events;if(U){D=Ia(p.value,U);p={stroke:Z,"stroke-width":U};if(fa)p.dashstyle=fa}else if(L(C)&&L(X)){C=Ga(C,J);X=nb(X,Q);H=Ia(X);if((D=Ia(C))&&H)D.push(H[4],H[5],H[1],H[2]);else D=null;p=
{fill:Z}}else return;if(L(S))p.zIndex=S;if(ja)if(D)ja.animate({d:D},null,ja.onGetPath);else{ja.hide();ja.onGetPath=function(){ja.show()}}else if(D&&D.length){l.svgElem=ja=$.path(D).attr(p).add();if(pc){fa=function(gb){ja.on(gb,function(Pb){pc[gb].apply(l,[Pb])})};for(la in pc)fa(la)}}if(r&&L(r.text)&&D&&D.length&&Ca>0&&ra>0){r=wa({align:O&&H&&"center",x:O?!H&&4:10,verticalAlign:!O&&H&&"middle",y:O?H?16:10:H?6:-4,rotation:O&&!H&&90},r);if(!o)l.label=o=$.text(r.text,0,0).attr({align:r.textAlign||r.align,
rotation:r.rotation,zIndex:S}).css(r.style).add();H=[D[1],D[4],D[6]||D[1]];D=[D[2],D[5],D[7]||D[2]];la=nb.apply(Ta,H);S=nb.apply(Ta,D);o.align(r,false,{x:la,y:S,width:Ga.apply(Ta,H)-la,height:Ga.apply(Ta,D)-S});o.show()}else o&&o.hide();return l},destroy:function(){for(var l in this){this[l]&&this[l].destroy&&this[l].destroy();delete this[l]}mc(Ob,this)}};ta=function(l,p,r,o){var U=1,X=0,H=o?ha:F;o=o?fb:J;H||(H=F);if(r){U*=-1;X=B}if(Yb){U*=-1;X-=U*B}if(p){if(Yb)l=B-l;l=l/H+o}else l=U*(l-o)*H+X;return l};
Ia=function(l,p,r){var o,U,X;l=ta(l,null,null,r);var H=r&&Oc||Oa,C=r&&hd||Va,fa;r=U=V(l+va);o=X=V(H-l-va);if(isNaN(l))fa=true;else if(O){o=aa;X=H-pb;if(r<W||r>W+Ca)fa=true}else{r=W;U=C-zb;if(o<aa||o>aa+ra)fa=true}return fa?null:$.crispLine([Wa,r,o,Ba,U,X],p||0)};if(Fa&&ka&&Yb===Qa)Yb=true;ma(s,{addPlotBand:sa,addPlotLine:sa,adjustTickAmount:function(){if(Eb&&!N&&!bb&&!Nb){var l=ec,p=pa.length;ec=Eb[I];if(p<ec){for(;pa.length<ec;)pa.push(M(pa[pa.length-1]+Ua));F*=(p-1)/(ec-1);Q=pa[pa.length-1]}if(L(l)&&
ec!=l)s.isDirty=true}},categories:bb,getExtremes:function(){return{min:J,max:Q,dataMin:Sa,dataMax:v}},getPlotLinePath:Ia,getThreshold:function(l){if(J>l)l=J;else if(Q<l)l=Q;return ta(l,0,1)},isXAxis:ka,options:h,plotLinesAndBands:Ob,getOffset:function(){var l=Y.length&&L(J)&&L(Q),p=0,r=0,o=h.title,U=h.labels,X=[-1,1,1,-1][G];if(!rb){rb=$.g("axis").attr({zIndex:7}).add();Fb=$.g("grid").attr({zIndex:1}).add()}fc=0;if(l||Nb){t(pa,function(C){if(qb[C])qb[C].addLabel();else qb[C]=new x(C);if(G===0||G==
2||{1:"left",3:"right"}[G]==U.align)fc=Ga(qb[C].getLabelSize(),fc)});if(Nc)fc+=(Nc-1)*16}else for(var H in qb){qb[H].destroy();delete qb[H]}if(o&&o.text){if(!s.axisTitle)s.axisTitle=$.text(o.text,0,0).attr({zIndex:7,rotation:o.rotation||0,align:o.textAlign||{low:"left",middle:"center",high:"right"}[o.align]}).css(o.style).add();p=s.axisTitle.getBBox()[O?"height":"width"];r=y(o.margin,O?5:10)}R=X*(h.offset||Qb[G]);ed=fc+(G!=2&&fc&&X*h.labels[O?"y":"x"])+r;Qb[G]=Ga(Qb[G],ed+p+X*R)},render:Ya,setCategories:function(l,
p){s.categories=bb=l;t(Y,function(r){r.translate();r.setTooltipPoints(true)});s.isDirty=true;y(p,true)&&m.redraw()},setExtremes:function(l,p,r,o){Kb(o,m);r=y(r,true);Ja(s,"setExtremes",{min:l,max:p},function(){na=l;Ma=p;r&&m.redraw()})},setScale:Da,setTickPositions:da,translate:ta,redraw:function(){gc.resetTracker&&gc.resetTracker();Ya();t(Ob,function(l){l.render()});t(Y,function(l){l.isDirty=true})},removePlotBand:Ha,removePlotLine:Ha,reversed:Yb,stacks:ca});for(gd in Md)Pa(s,gd,Md[gd]);Da()}function d(){var m=
{};return{add:function(h,x,w,P){if(!m[h]){x=$.text(x,0,0).css(a.toolbar.itemStyle).align({align:"right",x:-zb-20,y:aa+30}).on("click",P).attr({align:"right",zIndex:20}).add();m[h]=x}},remove:function(h){Fc(m[h].element);m[h]=null}}}function e(m){function h(){var I=this.points||nc(this),B=I[0].series.xAxis,F=this.x;B=B&&B.options.type=="datetime";var ha=Ib(F)||B,va;va=ha?['<span style="font-size: 10px">',B?Mc("%A, %b %e, %Y",F):F,"</span><br/>"]:[];t(I,function(ta){va.push(ta.point.tooltipFormatter(ha))});
return va.join("")}function x(I,B){G=ka?I:(2*G+I)/3;ca=ka?B:(ca+B)/2;s.translate(G,ca);id=ab(I-G)>1||ab(B-ca)>1?function(){x(I,B)}:null}function w(){if(!ka){var I=q.hoverPoints;s.hide();t(da,function(B){B&&B.hide()});I&&t(I,function(B){B.setState()});q.hoverPoints=null;ka=true}}var P,ga=m.borderWidth,M=m.crosshairs,da=[],Da=m.style,sa=m.shared,Ya=oa(Da.padding),Ha=ga+Ya,ka=true,Na,O,G=0,ca=0;Da.padding=0;var s=$.g("tooltip").attr({zIndex:8}).add(),N=$.rect(Ha,Ha,0,0,m.borderRadius,ga).attr({fill:m.backgroundColor,
"stroke-width":ga}).add(s).shadow(m.shadow),R=$.text("",Ya+Ha,oa(Da.fontSize)+Ya+Ha).attr({zIndex:1}).css(Da).add(s);s.hide();return{shared:sa,refresh:function(I){var B,F,ha,va=0,ta={},Ia=[];ha=I.tooltipPos;B=m.formatter||h;ta=q.hoverPoints;var rb=function(Ea){return{series:Ea.series,point:Ea,x:Ea.category,y:Ea.y,percentage:Ea.percentage,total:Ea.total||Ea.stackTotal}};if(sa){ta&&t(ta,function(Ea){Ea.setState()});q.hoverPoints=I;t(I,function(Ea){Ea.setState(xb);va+=Ea.plotY;Ia.push(rb(Ea))});F=I[0].plotX;
va=V(va)/I.length;ta={x:I[0].category};ta.points=Ia;I=I[0]}else ta=rb(I);ta=B.call(ta);P=I.series;F=sa?F:I.plotX;va=sa?va:I.plotY;B=V(ha?ha[0]:Fa?Ca-va:F);F=V(ha?ha[1]:Fa?ra-F:va);ha=sa||!I.series.isCartesian||hc(B,F);if(ta===false||!ha)w();else{if(ka){s.show();ka=false}R.attr({text:ta});ha=R.getBBox();Na=ha.width;O=ha.height;N.attr({width:Na+2*Ya,height:O+2*Ya,stroke:m.borderColor||I.color||P.color||"#606060"});B=B-Na+W-25;F=F-O+aa+10;if(B<7){B=7;F-=30}if(F<5)F=5;else if(F+O>Oa)F=Oa-O-5;x(V(B-Ha),
V(F-Ha))}if(M){M=nc(M);F=M.length;for(var Fb;F--;)if(M[F]&&(Fb=I.series[F?"yAxis":"xAxis"])){B=Fb.getPlotLinePath(I[F?"y":"x"],1);if(da[F])da[F].attr({d:B,visibility:Ab});else{ha={"stroke-width":M[F].width||1,stroke:M[F].color||"#C0C0C0",zIndex:2};if(M[F].dashStyle)ha.dashstyle=M[F].dashStyle;da[F]=$.path(B).attr(ha).add()}}}},hide:w}}function f(m,h){function x(G){var ca;G=G||hb.event;if(!G.target)G.target=G.srcElement;ca=G.touches?G.touches.item(0):G;if(G.type!="mousemove"||hb.opera){for(var s=ua,
N={left:s.offsetLeft,top:s.offsetTop};s=s.offsetParent;){N.left+=s.offsetLeft;N.top+=s.offsetTop;if(s!=za.body&&s!=za.documentElement){N.left-=s.scrollLeft;N.top-=s.scrollTop}}qc=N}if(Ac){G.chartX=G.x;G.chartY=G.y}else if(ca.layerX===Qa){G.chartX=ca.pageX-qc.left;G.chartY=ca.pageY-qc.top}else{G.chartX=G.layerX;G.chartY=G.layerY}return G}function w(G){var ca={xAxis:[],yAxis:[]};t(Xa,function(s){var N=s.translate,R=s.isXAxis;ca[R?"xAxis":"yAxis"].push({axis:s,value:N((Fa?!R:R)?G.chartX-W:ra-G.chartY+
aa,true)})});return ca}function P(){var G=m.hoverSeries,ca=m.hoverPoint;ca&&ca.onMouseOut();G&&G.onMouseOut();rc&&rc.hide();jd=null}function ga(){if(sa){var G={xAxis:[],yAxis:[]},ca=sa.getBBox(),s=ca.x-W,N=ca.y-aa;if(Da){t(Xa,function(R){var I=R.translate,B=R.isXAxis,F=Fa?!B:B,ha=I(F?s:ra-N-ca.height,true);I=I(F?s+ca.width:ra-N,true);G[B?"xAxis":"yAxis"].push({axis:R,min:nb(ha,I),max:Ga(ha,I)})});Ja(m,"selection",G,kd)}sa=sa.destroy()}m.mouseIsDown=ld=Da=false;Bb(za,Gb?"touchend":"mouseup",ga)}var M,
da,Da,sa,Ya=u.zoomType,Ha=/x/.test(Ya),ka=/y/.test(Ya),Na=Ha&&!Fa||ka&&Fa,O=ka&&!Fa||Ha&&Fa;Pc=function(){if(Qc){Qc.translate(W,aa);Fa&&Qc.attr({width:m.plotWidth,height:m.plotHeight}).invert()}else m.trackerGroup=Qc=$.g("tracker").attr({zIndex:9}).add()};Pc();if(h.enabled)m.tooltip=rc=e(h);(function(){var G=true;ua.onmousedown=function(s){s=x(s);m.mouseIsDown=ld=true;M=s.chartX;da=s.chartY;Pa(za,Gb?"touchend":"mouseup",ga)};var ca=function(s){if(!(s&&s.touches&&s.touches.length>1)){s=x(s);if(!Gb)s.returnValue=
false;var N=s.chartX,R=s.chartY,I=!hc(N-W,R-aa);if(Gb&&s.type=="touchstart")if(xa(s.target,"isTracker"))m.runTrackerClick||s.preventDefault();else!$d&&!I&&s.preventDefault();if(I){G||P();if(N<W)N=W;else if(N>W+Ca)N=W+Ca;if(R<aa)R=aa;else if(R>aa+ra)R=aa+ra}if(ld&&s.type!="touchstart"){if(Da=Math.sqrt(Math.pow(M-N,2)+Math.pow(da-R,2))>10){if(ic&&(Ha||ka)&&hc(M-W,da-aa))sa||(sa=$.rect(W,aa,Na?1:Ca,O?1:ra,0).attr({fill:"rgba(69,114,167,0.25)",zIndex:7}).add());if(sa&&Na){N=N-M;sa.attr({width:ab(N),x:(N>
0?0:N)+M})}if(sa&&O){R=R-da;sa.attr({height:ab(R),y:(R>0?0:R)+da})}}}else if(!I){var B;R=m.hoverPoint;N=m.hoverSeries;var F,ha,va=Va,ta=Fa?s.chartY:s.chartX-W;if(rc&&h.shared){B=[];F=Aa.length;for(ha=0;ha<F;ha++)if(Aa[ha].visible&&Aa[ha].tooltipPoints.length){s=Aa[ha].tooltipPoints[ta];s._dist=ab(ta-s.plotX);va=nb(va,s._dist);B.push(s)}for(F=B.length;F--;)B[F]._dist>va&&B.splice(F,1);if(B.length&&B[0].plotX!=jd){rc.refresh(B);jd=B[0].plotX}}if(N&&N.tracker)(s=N.tooltipPoints[ta])&&s!=R&&s.onMouseOver()}return(G=
I)||!ic}};ua.onmousemove=ca;Pa(ua,"mouseleave",P);ua.ontouchstart=function(s){if(Ha||ka)ua.onmousedown(s);ca(s)};ua.ontouchmove=ca;ua.ontouchend=function(){Da&&P()};ua.onclick=function(s){var N=m.hoverPoint;s=x(s);s.cancelBubble=true;if(!Da)if(N&&xa(s.target,"isTracker")){var R=N.plotX,I=N.plotY;ma(N,{pageX:qc.left+W+(Fa?Ca-I:R),pageY:qc.top+aa+(Fa?ra-R:I)});Ja(N.series,"click",ma(s,{point:N}));N.firePointEvent("click",s)}else{ma(s,w(s));hc(s.chartX-W,s.chartY-aa)&&Ja(m,"click",s)}Da=false}})();Nd=
setInterval(function(){id&&id()},32);ma(this,{zoomX:Ha,zoomY:ka,resetTracker:P})}function g(m){var h=m.type||u.type||u.defaultSeriesType,x=sb[h],w=q.hasRendered;if(w)if(Fa&&h=="column")x=sb.bar;else if(!Fa&&h=="bar")x=sb.column;h=new x;h.init(q,m);if(!w&&h.inverted)Fa=true;if(h.isCartesian)ic=h.isCartesian;Aa.push(h);return h}function i(){u.alignTicks!==false&&t(Xa,function(m){m.adjustTickAmount()});Eb=null}function j(m){var h=q.isDirtyLegend,x,w=q.isDirtyBox,P=Aa.length,ga=P,M=q.clipRect;for(Kb(m,
q);ga--;){m=Aa[ga];if(m.isDirty&&m.options.stacking){x=true;break}}if(x)for(ga=P;ga--;){m=Aa[ga];if(m.options.stacking)m.isDirty=true}t(Aa,function(da){if(da.isDirty){da.cleanData();da.getSegments();if(da.options.legendType=="point")h=true}});if(h&&md.renderLegend){md.renderLegend();q.isDirtyLegend=false}if(ic){if(!Rc){Eb=null;t(Xa,function(da){da.setScale()})}i();sc();t(Xa,function(da){if(da.isDirty||w){da.redraw();w=true}})}if(w){nd();Pc();if(M){Sc(M);M.animate({width:q.plotSizeX,height:q.plotSizeY})}}t(Aa,
function(da){if(da.isDirty&&da.visible&&(!da.isCartesian||da.xAxis))da.redraw()});gc&&gc.resetTracker&&gc.resetTracker();Ja(q,"redraw")}function k(){var m=a.xAxis||{},h=a.yAxis||{},x;m=nc(m);t(m,function(w,P){w.index=P;w.isX=true});h=nc(h);t(h,function(w,P){w.index=P});Xa=m.concat(h);q.xAxis=[];q.yAxis=[];Xa=jc(Xa,function(w){x=new c(q,w);q[x.isXAxis?"xAxis":"yAxis"].push(x);return x});i()}function n(m,h){kc=wa(a.title,m);tc=wa(a.subtitle,h);t([["title",m,kc],["subtitle",h,tc]],function(x){var w=
x[0],P=q[w],ga=x[1];x=x[2];if(P&&ga){P.destroy();P=null}if(x&&x.text&&!P)q[w]=$.text(x.text,0,0).attr({align:x.align,"class":"highcharts-"+w,zIndex:1}).css(x.style).add().align(x,false,uc)})}function z(){ib=u.renderTo;Od=$b+od++;if(Ib(ib))ib=za.getElementById(ib);ib.innerHTML="";if(!ib.offsetWidth){Rb=ib.cloneNode(0);La(Rb,{position:lc,top:"-9999px",display:""});za.body.appendChild(Rb)}Tc=(Rb||ib).offsetWidth;vc=(Rb||ib).offsetHeight;q.chartWidth=Va=u.width||Tc||600;q.chartHeight=Oa=u.height||(vc>
19?vc:400);q.container=ua=eb(Lb,{className:"highcharts-container"+(u.className?" "+u.className:""),id:Od},ma({position:Pd,overflow:tb,width:Va+Za,height:Oa+Za,textAlign:"left"},u.style),Rb||ib);q.renderer=$=u.renderer=="SVG"?new Uc(ua,Va,Oa):new Qd(ua,Va,Oa);var m,h;if(/Firefox/.test(wc)&&ua.getBoundingClientRect){m=function(){La(ua,{left:0,top:0});h=ua.getBoundingClientRect();La(ua,{left:-h.left%1+Za,top:-h.top%1+Za})};m();Pa(hb,"resize",m);Pa(q,"destroy",function(){Bb(hb,"resize",m)})}}function E(){function m(){var x=
u.width||ib.offsetWidth,w=u.height||ib.offsetHeight;if(x&&w){if(x!=Tc||w!=vc){clearTimeout(h);h=setTimeout(function(){pd(x,w,false)},100)}Tc=x;vc=w}}var h;Pa(window,"resize",m);Pa(q,"destroy",function(){Bb(window,"resize",m)})}function ia(){var m=a.labels,h=a.credits,x;n();md=q.legend=new ae(q);sc();t(Xa,function(w){w.setTickPositions(true)});i();sc();nd();ic&&t(Xa,function(w){w.render()});if(!q.seriesGroup)q.seriesGroup=$.g("series-group").attr({zIndex:3}).add();t(Aa,function(w){w.translate();w.setTooltipPoints();
w.render()});m.items&&t(m.items,function(){var w=ma(m.style,this.style),P=oa(w.left)+W,ga=oa(w.top)+aa+12;delete w.left;delete w.top;$.text(this.html,P,ga).attr({zIndex:2}).css(w).add()});if(!q.toolbar)q.toolbar=d(q);if(h.enabled&&!q.credits){x=h.href;$.text(h.text,0,0).on("click",function(){if(x)location.href=x}).attr({align:h.position.align,zIndex:8}).css(h.style).add().align(h.position)}Pc();q.hasRendered=true;if(Rb){ib.appendChild(ua);Fc(Rb)}}function T(){var m=Aa.length,h=ua&&ua.parentNode;Ja(q,
"destroy");Bb(hb,"unload",T);Bb(q);for(t(Xa,function(x){Bb(x)});m--;)Aa[m].destroy();ua.innerHTML="";Bb(ua);h&&h.removeChild(ua);ua=null;$.alignedObjects=null;clearInterval(Nd);for(m in q)delete q[m]}function K(){if(!xc&&!hb.parent&&za.readyState!="complete")za.attachEvent("onreadystatechange",function(){za.detachEvent("onreadystatechange",K);K()});else{z();qd();rd();t(a.series||[],function(m){g(m)});q.inverted=Fa=y(Fa,a.chart.inverted);k();q.render=ia;q.tracker=gc=new f(q,a.tooltip);ia();Ja(q,"load");
b&&b.apply(q,[q]);t(q.callbacks,function(m){m.apply(q,[q])})}}Lc=wa(Lc,Ra.xAxis);fd=wa(fd,Ra.yAxis);Ra.xAxis=Ra.yAxis=null;a=wa(Ra,a);var u=a.chart,A=u.margin;A=Jb(A)?A:[A,A,A,A];var ba=y(u.marginTop,A[0]),ya=y(u.marginRight,A[1]),ea=y(u.marginBottom,A[2]),qa=y(u.marginLeft,A[3]),$a=u.spacingTop,jb=u.spacingRight,sd=u.spacingBottom,Vc=u.spacingLeft,uc,kc,tc,aa,zb,pb,W,Qb,ib,Rb,ua,Od,Tc,vc,Va,Oa,hd,Oc,td,ud,vd,wd,q=this,$d=(A=u.events)&&!!A.click,xd,hc,rc,ld,ac,Rd,yd,ra,Ca,gc,Qc,Pc,md,Sb,Tb,qc,ic=
u.showAxes,Rc=0,Xa=[],Eb,Aa=[],Fa,$,id,Nd,jd,nd,sc,qd,rd,pd,kd,Sd,ae=function(m){function h(v,Y){var na=v.legendItem,Ma=v.legendLine,Q=v.legendSymbol,J=O.color,fb=Y?M.itemStyle.color:J;J=Y?v.color:J;na&&na.css({fill:fb});Ma&&Ma.attr({stroke:J});Q&&Q.attr({stroke:J,fill:J})}function x(v,Y,na){var Ma=v.legendItem,Q=v.legendLine,J=v.legendSymbol;v=v.checkbox;Ma&&Ma.attr({x:Y,y:na});Q&&Q.translate(Y,na-4);J&&J.attr({x:Y+J.xOff,y:na+J.yOff});if(v){v.x=Y;v.y=na}}function w(){t(Ya,function(v){var Y=v.checkbox;
Y&&La(Y,{left:Ia.attr("translateX")+v.legendItemWidth+Y.x-40+Za,top:Ia.attr("translateY")+Y.y-11+Za})})}function P(v){var Y,na,Ma,Q,J,fb=v.legendItem;Q=v.series||v;if(!fb){J=/^(bar|pie|area|column)$/.test(Q.type);v.legendItem=fb=$.text(M.labelFormatter.call(v),0,0).css(v.visible?ka:O).on("mouseover",function(){v.setState(xb);fb.css(Na)}).on("mouseout",function(){fb.css(v.visible?ka:O);v.setState()}).on("click",function(){var Wb=function(){v.setVisible()};v.firePointEvent?v.firePointEvent("legendItemClick",
null,Wb):Ja(v,"legendItemClick",null,Wb)}).attr({zIndex:2}).add(Ia);if(!J&&v.options&&v.options.lineWidth){var cc=v.options;Q={"stroke-width":cc.lineWidth,zIndex:2};if(cc.dashStyle)Q.dashstyle=cc.dashStyle;v.legendLine=$.path([Wa,-Da-sa,0,Ba,-sa,0]).attr(Q).add(Ia)}if(J)Y=$.rect(na=-Da-sa,Ma=-11,Da,12,2).attr({"stroke-width":0,zIndex:3}).add(Ia);else if(v.options&&v.options.marker&&v.options.marker.enabled)Y=$.symbol(v.symbol,na=-Da/2-sa,Ma=-4,v.options.marker.radius).attr(v.pointAttr[cb]).attr({zIndex:3}).add(Ia);
if(Y){Y.xOff=na;Y.yOff=Ma}v.legendSymbol=Y;h(v,v.visible);if(v.options&&v.options.showCheckbox){v.checkbox=eb("input",{type:"checkbox",checked:v.selected,defaultChecked:v.selected},M.itemCheckboxStyle,ua);Pa(v.checkbox,"click",function(Wb){Ja(v,"checkboxClick",{checked:Wb.target.checked},function(){v.select()})})}}Y=fb.getBBox();na=v.legendItemWidth=M.itemWidth||Da+sa+Y.width+ca;F=Y.height;if(da&&R-N+na>(Fb||Va-2*G-N)){R=N;I+=F}B=I;x(v,R,I);if(da)R+=na;else I+=F;rb=Fb||Ga(da?R-N:na,rb);Ya.push(v)}
function ga(){R=N;I=s;B=rb=0;Ya=[];Ia||(Ia=$.g("legend").attr({zIndex:7}).add());Sa&&Ea.reverse();t(Ea,function(Ma){if(Ma.options.showInLegend)t(Ma.options.legendType=="point"?Ma.data:[Ma],P)});Sa&&Ea.reverse();Sb=Fb||rb;Tb=B-s+F;if(va||ta){Sb+=2*G;Tb+=2*G;if(ha)Sb>0&&Tb>0&&ha.animate({width:Sb,height:Tb});else ha=$.rect(0,0,Sb,Tb,M.borderRadius,va||0).attr({stroke:M.borderColor,"stroke-width":va||0,fill:ta||mb}).add(Ia).shadow(M.shadow);ha[Ya.length?"show":"hide"]()}for(var v=["left","right","top",
"bottom"],Y,na=4;na--;){Y=v[na];if(Ha[Y]&&Ha[Y]!="auto"){M[na<2?"align":"verticalAlign"]=Y;M[na<2?"x":"y"]=oa(Ha[Y])*(na%2?-1:1)}}Ia.align(ma(M,{width:Sb,height:Tb}),true,uc);Rc||w()}var M=m.options.legend;if(M.enabled){var da=M.layout=="horizontal",Da=M.symbolWidth,sa=M.symbolPadding,Ya,Ha=M.style,ka=M.itemStyle,Na=M.itemHoverStyle,O=M.itemHiddenStyle,G=oa(Ha.padding),ca=20,s=18,N=4+G+Da+sa,R,I,B,F=0,ha,va=M.borderWidth,ta=M.backgroundColor,Ia,rb,Fb=M.width,Ea=m.series,Sa=M.reversed;ga();Pa(m,"endResize",
w);return{colorizeItem:h,destroyItem:function(v){var Y=v.checkbox;t(["legendItem","legendLine","legendSymbol"],function(na){v[na]&&v[na].destroy()});Y&&Fc(v.checkbox)},renderLegend:ga}}};hc=function(m,h){return m>=0&&m<=Ca&&h>=0&&h<=ra};Sd=function(){Ja(q,"selection",{resetSelection:true},kd);q.toolbar.remove("zoom")};kd=function(m){var h=Ra.lang,x=q.pointCount<100;q.toolbar.add("zoom",h.resetZoom,h.resetZoomTitle,Sd);!m||m.resetSelection?t(Xa,function(w){w.setExtremes(null,null,false,x)}):t(m.xAxis.concat(m.yAxis),
function(w){var P=w.axis;if(q.tracker[P.isXAxis?"zoomX":"zoomY"])P.setExtremes(w.min,w.max,false,x)});j()};sc=function(){var m=a.legend,h=y(m.margin,10),x=m.x,w=m.y,P=m.align,ga=m.verticalAlign,M;qd();if((q.title||q.subtitle)&&!L(ba))if(M=Ga(q.title&&!kc.floating&&!kc.verticalAlign&&kc.y||0,q.subtitle&&!tc.floating&&!tc.verticalAlign&&tc.y||0))aa=Ga(aa,M+y(kc.margin,15)+$a);if(m.enabled&&!m.floating)if(P=="right")L(ya)||(zb=Ga(zb,Sb-x+h+jb));else if(P=="left")L(qa)||(W=Ga(W,Sb+x+h+Vc));else if(ga==
"top")L(ba)||(aa=Ga(aa,Tb+w+h+$a));else if(ga=="bottom")L(ea)||(pb=Ga(pb,Tb-w+h+sd));ic&&t(Xa,function(da){da.getOffset()});L(qa)||(W+=Qb[3]);L(ba)||(aa+=Qb[0]);L(ea)||(pb+=Qb[2]);L(ya)||(zb+=Qb[1]);rd()};pd=function(m,h,x){var w=q.title,P=q.subtitle;Rc+=1;Kb(x,q);Oc=Oa;hd=Va;Va=V(m);Oa=V(h);La(ua,{width:Va+Za,height:Oa+Za});$.setSize(Va,Oa,x);Ca=Va-W-zb;ra=Oa-aa-pb;Eb=null;t(Xa,function(ga){ga.isDirty=true;ga.setScale()});t(Aa,function(ga){ga.isDirty=true});q.isDirtyLegend=true;q.isDirtyBox=true;
sc();w&&w.align(null,null,uc);P&&P.align(null,null,uc);j(x);Oc=null;Ja(q,"resize");setTimeout(function(){Ja(q,"endResize",null,function(){Rc-=1})},Bc&&Bc.duration||500)};rd=function(){q.plotLeft=W=V(W);q.plotTop=aa=V(aa);q.plotWidth=Ca=V(Va-W-zb);q.plotHeight=ra=V(Oa-aa-pb);q.plotSizeX=Fa?ra:Ca;q.plotSizeY=Fa?Ca:ra;uc={x:Vc,y:$a,width:Va-Vc-jb,height:Oa-$a-sd}};qd=function(){aa=y(ba,$a);zb=y(ya,jb);pb=y(ea,sd);W=y(qa,Vc);Qb=[0,0,0,0]};nd=function(){var m=u.borderWidth||0,h=u.backgroundColor,x=u.plotBackgroundColor,
w=u.plotBackgroundImage,P,ga={x:W,y:aa,width:Ca,height:ra};P=m+(u.shadow?8:0);if(m||h)if(td)td.animate({width:Va-P,height:Oa-P});else td=$.rect(P/2,P/2,Va-P,Oa-P,u.borderRadius,m).attr({stroke:u.borderColor,"stroke-width":m,fill:h||mb}).add().shadow(u.shadow);if(x)if(ud)ud.animate(ga);else ud=$.rect(W,aa,Ca,ra,0).attr({fill:x}).add().shadow(u.plotShadow);if(w)if(vd)vd.animate(ga);else vd=$.image(w,W,aa,Ca,ra).add();if(u.plotBorderWidth)if(wd)wd.animate(ga);else wd=$.rect(W,aa,Ca,ra,0,u.plotBorderWidth).attr({stroke:u.plotBorderColor,
"stroke-width":u.plotBorderWidth,zIndex:4}).add();q.isDirtyBox=false};Wc=Hb=0;Pa(hb,"unload",T);u.reflow!==false&&Pa(q,"load",E);if(A)for(xd in A)Pa(q,xd,A[xd]);q.options=a;q.series=Aa;q.addSeries=function(m,h,x){var w;if(m){Kb(x,q);h=y(h,true);Ja(q,"addSeries",{options:m},function(){w=g(m);w.isDirty=true;q.isDirtyLegend=true;h&&q.redraw()})}return w};q.animation=y(u.animation,true);q.destroy=T;q.get=function(m){var h,x,w;for(h=0;h<Xa.length;h++)if(Xa[h].options.id==m)return Xa[h];for(h=0;h<Aa.length;h++)if(Aa[h].options.id==
m)return Aa[h];for(h=0;h<Aa.length;h++){w=Aa[h].data;for(x=0;x<w.length;x++)if(w[x].id==m)return w[x]}return null};q.getSelectedPoints=function(){var m=[];t(Aa,function(h){m=m.concat(zd(h.data,function(x){return x.selected}))});return m};q.getSelectedSeries=function(){return zd(Aa,function(m){return m.selected})};q.hideLoading=function(){Xc(ac,{opacity:0},{duration:a.loading.hideDuration,complete:function(){La(ac,{display:mb})}});yd=false};q.isInsidePlot=hc;q.redraw=j;q.setSize=pd;q.setTitle=n;q.showLoading=
function(m){var h=a.loading;if(!ac){ac=eb(Lb,{className:"highcharts-loading"},ma(h.style,{left:W+Za,top:aa+Za,width:Ca+Za,height:ra+Za,zIndex:10,display:mb}),ua);Rd=eb("span",null,h.labelStyle,ac)}Rd.innerHTML=m||a.lang.loading;if(!yd){La(ac,{opacity:0,display:""});Xc(ac,{opacity:h.style.opacity},{duration:h.showDuration});yd=true}};q.pointCount=0;K()}var za=document,hb=window,Ta=Math,V=Ta.round,Mb=Ta.floor,dd=Ta.ceil,Ga=Ta.max,nb=Ta.min,ab=Ta.abs,ub=Ta.cos,yb=Ta.sin,Ub=Ta.PI,Td=Ub*2/360,wc=navigator.userAgent,
Ac=/msie/i.test(wc)&&!hb.opera,yc=za.documentMode==8,be=/AppleWebKit/.test(wc),xc=hb.SVGAngle||za.implementation.hasFeature("http://www.w3.org/TR/SVG11/feature#BasicStructure","1.1"),Gb="ontouchstart"in za.documentElement,Hb,Wc,ce={},od=0,ob=1,Gc,Ra,Mc,Bc,Yc,Qa,Lb="div",lc="absolute",Pd="relative",tb="hidden",$b="highcharts-",Ab="visible",Za="px",mb="none",Wa="M",Ba="L",Ud="rgba(192,192,192,"+(xc?1.0E-6:0.0020)+")",cb="",xb="hover",Cc,$c,ad,bd,oc,Dc,Ec,Cd,Dd,cd,Ed,Fd,db=hb.HighchartsAdapter,Cb=db||
{},t=Cb.each,zd=Cb.grep,jc=Cb.map,wa=Cb.merge,Ad=Cb.hyphenate,Pa=Cb.addEvent,Bb=Cb.removeEvent,Ja=Cb.fireEvent,Xc=Cb.animate,Sc=Cb.stop,sb={};db&&db.init&&db.init();if(!db&&hb.jQuery){var kb=jQuery;t=function(a,b){for(var c=0,d=a.length;c<d;c++)if(b.call(a[c],a[c],c,a)===false)return c};zd=kb.grep;jc=function(a,b){for(var c=[],d=0,e=a.length;d<e;d++)c[d]=b.call(a[d],a[d],d,a);return c};wa=function(){var a=arguments;return kb.extend(true,null,a[0],a[1],a[2],a[3])};Ad=function(a){return a.replace(/([A-Z])/g,
function(b,c){return"-"+c.toLowerCase()})};Pa=function(a,b,c){kb(a).bind(b,c)};Bb=function(a,b,c){var d=za.removeEventListener?"removeEventListener":"detachEvent";if(za[d]&&!a[d])a[d]=function(){};kb(a).unbind(b,c)};Ja=function(a,b,c,d){var e=kb.Event(b),f="detached"+b;ma(e,c);if(a[b]){a[f]=a[b];a[b]=null}kb(a).trigger(e);if(a[f]){a[b]=a[f];a[f]=null}d&&!e.isDefaultPrevented()&&d(e)};Xc=function(a,b,c){var d=kb(a);if(b.d){a.toD=b.d;b.d=1}d.stop();d.animate(b,c)};Sc=function(a){kb(a).stop()};kb.extend(kb.easing,
{easeOutQuad:function(a,b,c,d,e){return-d*(b/=e)*(b-2)+c}});var de=jQuery.fx.step._default,ee=jQuery.fx.prototype.cur;kb.fx.step._default=function(a){var b=a.elem;b.attr?b.attr(a.prop,a.now):de.apply(this,arguments)};kb.fx.step.d=function(a){var b=a.elem;if(!a.started){var c=Yc.init(b,b.d,b.toD);a.start=c[0];a.end=c[1];a.started=true}b.attr("d",Yc.step(a.start,a.end,a.pos,b.toD))};kb.fx.prototype.cur=function(){var a=this.elem;return a.attr?a.attr(this.prop):ee.apply(this,arguments)}}Yc={init:function(a,
b,c){b=b||"";var d=a.shift,e=b.indexOf("C")>-1,f=e?7:3,g;b=b.split(" ");c=[].concat(c);var i,j,k=function(n){for(g=n.length;g--;)n[g]==Wa&&n.splice(g+1,0,n[g+1],n[g+2],n[g+1],n[g+2])};if(e){k(b);k(c)}if(a.isArea){i=b.splice(b.length-6,6);j=c.splice(c.length-6,6)}if(d){c=[].concat(c).splice(0,f).concat(c);a.shift=false}if(b.length)for(a=c.length;b.length<a;){d=[].concat(b).splice(b.length-f,f);if(e){d[f-6]=d[f-2];d[f-5]=d[f-1]}b=b.concat(d)}if(i){b=b.concat(i);c=c.concat(j)}return[b,c]},step:function(a,
b,c,d){var e=[],f=a.length;if(c==1)e=d;else if(f==b.length&&c<1)for(;f--;){d=parseFloat(a[f]);e[f]=isNaN(d)?a[f]:c*parseFloat(b[f]-d)+d}else e=b;return e}};db={enabled:true,align:"center",x:0,y:15,style:{color:"#666",fontSize:"11px",lineHeight:"14px"}};Ra={colors:["#4572A7","#AA4643","#89A54E","#80699B","#3D96AE","#DB843D","#92A8CD","#A47D7C","#B5CA92"],symbols:["circle","diamond","square","triangle","triangle-down"],lang:{loading:"Loading...",months:["January","February","March","April","May","June",
"July","August","September","October","November","December"],weekdays:["Sunday","Monday","Tuesday","Wednesday","Thursday","Friday","Saturday"],decimalPoint:".",resetZoom:"Reset zoom",resetZoomTitle:"Reset zoom level 1:1",thousandsSep:","},global:{useUTC:true},chart:{borderColor:"#4572A7",borderRadius:5,defaultSeriesType:"line",ignoreHiddenSeries:true,spacingTop:10,spacingRight:10,spacingBottom:15,spacingLeft:10,style:{fontFamily:'"Lucida Grande", "Lucida Sans Unicode", Verdana, Arial, Helvetica, sans-serif',
fontSize:"12px"},backgroundColor:"#FFFFFF",plotBorderColor:"#C0C0C0"},title:{text:"Chart title",align:"center",y:15,style:{color:"#3E576F",fontSize:"16px"}},subtitle:{text:"",align:"center",y:30,style:{color:"#6D869F"}},plotOptions:{line:{allowPointSelect:false,showCheckbox:false,animation:{duration:1E3},events:{},lineWidth:2,shadow:true,marker:{enabled:true,lineWidth:0,radius:4,lineColor:"#FFFFFF",states:{hover:{},select:{fillColor:"#FFFFFF",lineColor:"#000000",lineWidth:2}}},point:{events:{}},dataLabels:wa(db,
{enabled:false,y:-6,formatter:function(){return this.y}}),showInLegend:true,states:{hover:{marker:{}},select:{marker:{}}},stickyTracking:true}},labels:{style:{position:lc,color:"#3E576F"}},legend:{enabled:true,align:"center",layout:"horizontal",labelFormatter:function(){return this.name},borderWidth:1,borderColor:"#909090",borderRadius:5,shadow:false,style:{padding:"5px"},itemStyle:{cursor:"pointer",color:"#3E576F"},itemHoverStyle:{cursor:"pointer",color:"#000000"},itemHiddenStyle:{color:"#C0C0C0"},
itemCheckboxStyle:{position:lc,width:"13px",height:"13px"},symbolWidth:16,symbolPadding:5,verticalAlign:"bottom",x:0,y:0},loading:{hideDuration:100,labelStyle:{fontWeight:"bold",position:Pd,top:"1em"},showDuration:100,style:{position:lc,backgroundColor:"white",opacity:0.5,textAlign:"center"}},tooltip:{enabled:true,backgroundColor:"rgba(255, 255, 255, .85)",borderWidth:2,borderRadius:5,shadow:true,snap:Gb?25:10,style:{color:"#333333",fontSize:"12px",padding:"5px",whiteSpace:"nowrap"}},toolbar:{itemStyle:{color:"#4572A7",
cursor:"pointer"}},credits:{enabled:true,text:"Highcharts.com",href:"http://www.highcharts.com",position:{align:"right",x:-10,verticalAlign:"bottom",y:-5},style:{cursor:"pointer",color:"#909090",fontSize:"10px"}}};var Lc={dateTimeLabelFormats:{second:"%H:%M:%S",minute:"%H:%M",hour:"%H:%M",day:"%e. %b",week:"%e. %b",month:"%b '%y",year:"%Y"},endOnTick:false,gridLineColor:"#C0C0C0",labels:db,lineColor:"#C0D0E0",lineWidth:1,max:null,min:null,minPadding:0.01,maxPadding:0.01,minorGridLineColor:"#E0E0E0",
minorGridLineWidth:1,minorTickColor:"#A0A0A0",minorTickLength:2,minorTickPosition:"outside",startOfWeek:1,startOnTick:false,tickColor:"#C0D0E0",tickLength:5,tickmarkPlacement:"between",tickPixelInterval:100,tickPosition:"outside",tickWidth:1,title:{align:"middle",style:{color:"#6D869F",fontWeight:"bold"}},type:"linear"},fd=wa(Lc,{endOnTick:true,gridLineWidth:1,tickPixelInterval:72,showLastLabel:true,labels:{align:"right",x:-8,y:3},lineWidth:0,maxPadding:0.05,minPadding:0.05,startOnTick:true,tickWidth:0,
title:{rotation:270,text:"Y-values"}}),Yd={labels:{align:"right",x:-8,y:null},title:{rotation:270}},Xd={labels:{align:"left",x:8,y:null},title:{rotation:90}},Ld={labels:{align:"center",x:0,y:14},title:{rotation:0}},Wd=wa(Ld,{labels:{y:-5}}),vb=Ra.plotOptions;db=vb.line;vb.spline=wa(db);vb.scatter=wa(db,{lineWidth:0,states:{hover:{lineWidth:0}}});vb.area=wa(db,{});vb.areaspline=wa(vb.area);vb.column=wa(db,{borderColor:"#FFFFFF",borderWidth:1,borderRadius:0,groupPadding:0.2,marker:null,pointPadding:0.1,
minPointLength:0,states:{hover:{brightness:0.1,shadow:false},select:{color:"#C0C0C0",borderColor:"#000000",shadow:false}}});vb.bar=wa(vb.column,{dataLabels:{align:"left",x:5,y:0}});vb.pie=wa(db,{borderColor:"#FFFFFF",borderWidth:1,center:["50%","50%"],colorByPoint:true,dataLabels:{distance:30,enabled:true,formatter:function(){return this.point.name},y:5},legendType:"point",marker:null,size:"75%",showInLegend:false,slicedOffset:10,states:{hover:{brightness:0.1,shadow:false}}});Bd();var Vb=function(a){var b=
[],c;(function(d){if(c=/rgba\(\s*([0-9]{1,3})\s*,\s*([0-9]{1,3})\s*,\s*([0-9]{1,3})\s*,\s*([0-9]?(?:\.[0-9]+)?)\s*\)/.exec(d))b=[oa(c[1]),oa(c[2]),oa(c[3]),parseFloat(c[4],10)];else if(c=/#([a-fA-F0-9]{2})([a-fA-F0-9]{2})([a-fA-F0-9]{2})/.exec(d))b=[oa(c[1],16),oa(c[2],16),oa(c[3],16),1]})(a);return{get:function(d){return b&&!isNaN(b[0])?d=="rgb"?"rgb("+b[0]+","+b[1]+","+b[2]+")":d=="a"?b[3]:"rgba("+b.join(",")+")":a},brighten:function(d){if(bc(d)&&d!==0){var e;for(e=0;e<3;e++){b[e]+=oa(d*255);if(b[e]<
0)b[e]=0;if(b[e]>255)b[e]=255}}return this},setOpacity:function(d){b[3]=d;return this}}};Mc=function(a,b,c){function d(E){return E.toString().replace(/^([0-9])$/,"0$1")}if(!L(b)||isNaN(b))return"Invalid date";a=y(a,"%Y-%m-%d %H:%M:%S");b=new Date(b*ob);var e=b[ad](),f=b[bd](),g=b[oc](),i=b[Dc](),j=b[Ec](),k=Ra.lang,n=k.weekdays;k=k.months;b={a:n[f].substr(0,3),A:n[f],d:d(g),e:g,b:k[i].substr(0,3),B:k[i],m:d(i+1),y:j.toString().substr(2,2),Y:j,H:d(e),I:d(e%12||12),l:e%12||12,M:d(b[$c]()),p:e<12?"AM":
"PM",P:e<12?"am":"pm",S:d(b.getSeconds())};for(var z in b)a=a.replace("%"+z,b[z]);return c?a.substr(0,1).toUpperCase()+a.substr(1):a};Hc.prototype={init:function(a,b){this.element=za.createElementNS("http://www.w3.org/2000/svg",b);this.renderer=a},animate:function(a,b,c){if(b=y(b,Bc,true)){b=wa(b);if(c)b.complete=c;Xc(this,a,b)}else{this.attr(a);c&&c()}},attr:function(a,b){var c,d,e,f,g=this.element,i=g.nodeName,j=this.renderer,k,n=this.shadows,z,E=this;if(Ib(a)&&L(b)){c=a;a={};a[c]=b}if(Ib(a)){c=
a;if(i=="circle")c={x:"cx",y:"cy"}[c]||c;else if(c=="strokeWidth")c="stroke-width";E=xa(g,c)||this[c]||0;if(c!="d"&&c!="visibility")E=parseFloat(E)}else for(c in a){k=false;d=a[c];if(c=="d"){if(d&&d.join)d=d.join(" ");if(/(NaN| {2}|^$)/.test(d))d="M 0 0";this.d=d}else if(c=="x"&&i=="text"){for(e=0;e<g.childNodes.length;e++){f=g.childNodes[e];xa(f,"x")==xa(g,"x")&&xa(f,"x",d)}if(this.rotation)xa(g,"transform","rotate("+this.rotation+" "+d+" "+oa(a.y||xa(g,"y"))+")")}else if(c=="fill")d=j.color(d,g,
c);else if(i=="circle"&&(c=="x"||c=="y"))c={x:"cx",y:"cy"}[c]||c;else if(c=="translateX"||c=="translateY"||c=="rotation"||c=="verticalAlign"){this[c]=d;this.updateTransform();k=true}else if(c=="stroke")d=j.color(d,g,c);else if(c=="dashstyle"){c="stroke-dasharray";if(d){d=d.toLowerCase().replace("shortdashdotdot","3,1,1,1,1,1,").replace("shortdashdot","3,1,1,1").replace("shortdot","1,1,").replace("shortdash","3,1,").replace("longdash","8,3,").replace(/dot/g,"1,3,").replace("dash","4,3,").replace(/,$/,
"").split(",");for(e=d.length;e--;)d[e]=oa(d[e])*a["stroke-width"];d=d.join(",")}}else if(c=="isTracker")this[c]=d;else if(c=="width")d=oa(d);else if(c=="align"){c="text-anchor";d={left:"start",center:"middle",right:"end"}[d]}if(c=="strokeWidth")c="stroke-width";if(be&&c=="stroke-width"&&d===0)d=1.0E-6;if(this.symbolName&&/^(x|y|r|start|end|innerR)/.test(c)){if(!z){this.symbolAttr(a);z=true}k=true}if(n&&/^(width|height|visibility|x|y|d)$/.test(c))for(e=n.length;e--;)xa(n[e],c,d);if(c=="text"){this.textStr=
d;j.buildText(this)}else k||xa(g,c,d)}return E},symbolAttr:function(a){this.x=y(a.x,this.x);this.y=y(a.y,this.y);this.r=y(a.r,this.r);this.start=y(a.start,this.start);this.end=y(a.end,this.end);this.width=y(a.width,this.width);this.height=y(a.height,this.height);this.innerR=y(a.innerR,this.innerR);this.attr({d:this.renderer.symbols[this.symbolName](this.x,this.y,this.r,{start:this.start,end:this.end,width:this.width,height:this.height,innerR:this.innerR})})},clip:function(a){return this.attr("clip-path",
"url("+this.renderer.url+"#"+a.id+")")},css:function(a){var b=this.element;if(a&&a.color)a.fill=a.color;a=ma(this.styles,a);Ac&&!xc?La(this.element,a):this.attr({style:Vd(a)});this.styles=a;a.width&&b.nodeName=="text"&&this.added&&this.renderer.buildText(this);return this},on:function(a,b){var c=b;if(Gb&&a=="click"){a="touchstart";c=function(d){d.preventDefault();b()}}this.element["on"+a]=c;return this},translate:function(a,b){return this.attr({translateX:a,translateY:b})},invert:function(){this.inverted=
true;this.updateTransform();return this},updateTransform:function(){var a=this.translateX||0,b=this.translateY||0,c=this.inverted,d=this.rotation,e=[];if(c){a+=this.attr("width");b+=this.attr("height")}if(a||b)e.push("translate("+a+","+b+")");if(c)e.push("rotate(90) scale(-1,1)");else d&&e.push("rotate("+d+" "+this.x+" "+this.y+")");e.length&&xa(this.element,"transform",e.join(" "))},toFront:function(){var a=this.element;a.parentNode.appendChild(a);return this},align:function(a,b,c){if(a){this.alignOptions=
a;this.alignByTranslate=b;c||this.renderer.alignedObjects.push(this)}else{a=this.alignOptions;b=this.alignByTranslate}c=y(c,this.renderer);var d=a.align,e=a.verticalAlign,f=(c.x||0)+(a.x||0),g=(c.y||0)+(a.y||0),i={};if(/^(right|center)$/.test(d))f+=(c.width-(a.width||0))/{right:1,center:2}[d];i[b?"translateX":"x"]=f;if(/^(bottom|middle)$/.test(e))g+=(c.height-(a.height||0))/({bottom:1,middle:2}[e]||1);i[b?"translateY":"y"]=g;this[this.placed?"animate":"attr"](i);this.placed=true;return this},getBBox:function(){var a,
b,c,d=this.rotation,e=d*Td;try{a=ma({},this.element.getBBox())}catch(f){a={width:0,height:0}}b=a.width;c=a.height;if(d){a.width=ab(c*yb(e))+ab(b*ub(e));a.height=ab(c*ub(e))+ab(b*yb(e))}return a},show:function(){return this.attr({visibility:Ab})},hide:function(){return this.attr({visibility:tb})},add:function(a){var b=this.renderer,c=a||b,d=c.element||b.box,e=d.childNodes,f=this.element,g=xa(f,"zIndex"),i=this.textStr,j;this.parentInverted=a&&a.inverted;if(g){c.handleZ=true;g=oa(g)}if(c.handleZ)for(j=
0;j<e.length;j++){a=e[j];c=xa(a,"zIndex");if(a!=f&&(oa(c)>g||!L(g)&&L(c))){d.insertBefore(f,a);return this}}if(i!==undefined){b.buildText(this);this.added=true}d.appendChild(f);return this},destroy:function(){var a=this.element||{},b=this.shadows,c=a.parentNode,d;a.onclick=a.onmouseout=a.onmouseover=a.onmousemove=null;Sc(this);c&&c.removeChild(a);b&&t(b,function(e){(c=e.parentNode)&&c.removeChild(e)});mc(this.renderer.alignedObjects,this);for(d in this)delete this[d];return null},empty:function(){for(var a=
this.element,b=a.childNodes,c=b.length;c--;)a.removeChild(b[c])},shadow:function(a){var b=[],c,d=this.element,e=this.parentInverted?"(-1,-1)":"(1,1)";if(a){for(a=1;a<=3;a++){c=d.cloneNode(0);xa(c,{isShadow:"true",stroke:"rgb(0, 0, 0)","stroke-opacity":0.05*a,"stroke-width":7-2*a,transform:"translate"+e,fill:mb});d.parentNode.insertBefore(c,d);b.push(c)}this.shadows=b}return this}};var Uc=function(){this.init.apply(this,arguments)};Uc.prototype={init:function(a,b,c){var d=location,e;this.Element=Hc;
e=this.createElement("svg").attr({xmlns:"http://www.w3.org/2000/svg",version:"1.1"});a.appendChild(e.element);this.box=e.element;this.boxWrapper=e;this.alignedObjects=[];this.url=Ac?"":d.href.replace(/#.*?$/,"");this.defs=this.createElement("defs").add();this.setSize(b,c,false)},createElement:function(a){var b=new this.Element;b.init(this,a);return b},buildText:function(a){var b=a.element,c=y(a.textStr,"").toString().replace(/<(b|strong)>/g,'<span style="font-weight:bold">').replace(/<(i|em)>/g,'<span style="font-style:italic">').replace(/<a/g,
"<span").replace(/<\/(b|strong|i|em|a)>/g,"</span>").split(/<br[^>]?>/g),d=b.childNodes,e=/style="([^"]+)"/,f=/href="([^"]+)"/,g=xa(b,"x"),i=(a=a.styles)&&oa(a.width),j=a&&a.lineHeight,k;for(a=d.length;a--;)b.removeChild(d[a]);i&&this.box.appendChild(b);t(c,function(n,z){var E,ia=0,T;n=n.replace(/<span/g,"|||<span").replace(/<\/span>/g,"</span>|||");E=n.split("|||");t(E,function(K){if(K!==""||E.length==1){var u={},A=za.createElementNS("http://www.w3.org/2000/svg","tspan");e.test(K)&&xa(A,"style",
K.match(e)[1].replace(/(;| |^)color([ :])/,"$1fill$2"));if(f.test(K)){xa(A,"onclick",'location.href="'+K.match(f)[1]+'"');La(A,{cursor:"pointer"})}K=K.replace(/<(.|\n)*?>/g,"")||" ";A.appendChild(za.createTextNode(K));if(ia)u.dx=3;else u.x=g;if(!ia){if(z){T=oa(window.getComputedStyle(k,null).getPropertyValue("line-height"));if(isNaN(T))T=j||k.offsetHeight||18;xa(A,"dy",T)}k=A}xa(A,u);b.appendChild(A);ia++;if(i){K=K.replace(/-/g,"- ").split(" ");for(var ba,ya=[];K.length||ya.length;){ba=b.getBBox().width;
u=ba>i;if(!u||K.length==1){K=ya;ya=[];A=za.createElementNS("http://www.w3.org/2000/svg","tspan");xa(A,{x:g,dy:j||16});b.appendChild(A);if(ba>i)i=ba}else{A.removeChild(A.firstChild);ya.unshift(K.pop())}A.appendChild(za.createTextNode(K.join(" ").replace(/- /g,"-")))}}}})})},crispLine:function(a,b){if(a[1]==a[4])a[1]=a[4]=V(a[1])+b%2/2;if(a[2]==a[5])a[2]=a[5]=V(a[2])+b%2/2;return a},path:function(a){return this.createElement("path").attr({d:a,fill:mb})},circle:function(a,b,c){a=Jb(a)?a:{x:a,y:b,r:c};
return this.createElement("circle").attr(a)},arc:function(a,b,c,d,e,f){if(Jb(a)){b=a.y;c=a.r;d=a.innerR;e=a.start;f=a.end;a=a.x}return this.symbol("arc",a||0,b||0,c||0,{innerR:d||0,start:e||0,end:f||0})},rect:function(a,b,c,d,e,f){if(arguments.length>1){var g=(f||0)%2/2;a=V(a||0)+g;b=V(b||0)+g;c=V((c||0)-2*g);d=V((d||0)-2*g)}g=Jb(a)?a:{x:a,y:b,width:Ga(c,0),height:Ga(d,0)};return this.createElement("rect").attr(ma(g,{rx:e||g.r,ry:e||g.r,fill:mb}))},setSize:function(a,b,c){var d=this.alignedObjects,
e=d.length;this.width=a;this.height=b;for(this.boxWrapper[y(c,true)?"animate":"attr"]({width:a,height:b});e--;)d[e].align()},g:function(a){return this.createElement("g").attr(L(a)&&{"class":$b+a})},image:function(a,b,c,d,e){var f={preserveAspectRatio:mb};arguments.length>1&&ma(f,{x:b,y:c,width:d,height:e});f=this.createElement("image").attr(f);f.element.setAttributeNS("http://www.w3.org/1999/xlink","href",a);return f},symbol:function(a,b,c,d,e){var f,g=this.symbols[a];g=g&&g(b,c,d,e);var i=/^url\((.*?)\)$/;
if(g){f=this.path(g);ma(f,{symbolName:a,x:b,y:c,r:d});e&&ma(f,e)}else if(i.test(a)){a=a.match(i)[1];f=this.image(a).attr({x:b,y:c});eb("img",{onload:function(){var j=ce[this.src]||[this.width,this.height];f.attr({width:j[0],height:j[1]}).translate(-V(j[0]/2),-V(j[1]/2))},src:a})}else f=this.circle(b,c,d);return f},symbols:{square:function(a,b,c){c=0.707*c;return[Wa,a-c,b-c,Ba,a+c,b-c,a+c,b+c,a-c,b+c,"Z"]},triangle:function(a,b,c){return[Wa,a,b-1.33*c,Ba,a+c,b+0.67*c,a-c,b+0.67*c,"Z"]},"triangle-down":function(a,
b,c){return[Wa,a,b+1.33*c,Ba,a-c,b-0.67*c,a+c,b-0.67*c,"Z"]},diamond:function(a,b,c){return[Wa,a,b-c,Ba,a+c,b,a,b+c,a-c,b,"Z"]},arc:function(a,b,c,d){var e=d.start,f=d.end-1.0E-6,g=d.innerR,i=ub(e),j=yb(e),k=ub(f);f=yb(f);d=d.end-e<Ub?0:1;return[Wa,a+c*i,b+c*j,"A",c,c,0,d,1,a+c*k,b+c*f,Ba,a+g*k,b+g*f,"A",g,g,0,d,0,a+g*i,b+g*j,"Z"]}},clipRect:function(a,b,c,d){var e=$b+od++,f=this.createElement("clipPath").attr({id:e}).add(this.defs);a=this.rect(a,b,c,d,0).add(f);a.id=e;return a},color:function(a,
b,c){var d,e=/^rgba/;if(a&&a.linearGradient){var f=this;b=a.linearGradient;c=$b+od++;var g,i,j;g=f.createElement("linearGradient").attr({id:c,gradientUnits:"userSpaceOnUse",x1:b[0],y1:b[1],x2:b[2],y2:b[3]}).add(f.defs);t(a.stops,function(k){if(e.test(k[1])){d=Vb(k[1]);i=d.get("rgb");j=d.get("a")}else{i=k[1];j=1}f.createElement("stop").attr({offset:k[0],"stop-color":i,"stop-opacity":j}).add(g)});return"url("+this.url+"#"+c+")"}else if(e.test(a)){d=Vb(a);xa(b,c+"-opacity",d.get("a"));return d.get("rgb")}else return a},
text:function(a,b,c){var d=Ra.chart.style;b=V(y(b,0));c=V(y(c,0));a=this.createElement("text").attr({x:b,y:c,text:a}).css({"font-family":d.fontFamily,"font-size":d.fontSize});a.x=b;a.y=c;return a}};var Ka;if(!xc){var fe=wb(Hc,{init:function(a,b){var c=["<",b,' filled="f" stroked="f"'],d=["position: ",lc,";"];if(b=="shape"||b==Lb)d.push("left:0;top:0;width:10px;height:10px;");if(yc)d.push("visibility: ",b==Lb?tb:Ab);c.push(' style="',d.join(""),'"/>');if(b){c=b==Lb||b=="span"||b=="img"?c.join(""):
a.prepVML(c);this.element=eb(c)}this.renderer=a},add:function(a){var b=this.renderer,c=this.element,d=b.box;d=a?a.element||a:d;a&&a.inverted&&b.invertChild(c,d);yc&&d.gVis==tb&&La(c,{visibility:tb});d.appendChild(c);this.added=true;this.alignOnAdd&&this.updateTransform();return this},attr:function(a,b){var c,d,e,f=this.element||{},g=f.style,i=f.nodeName,j=this.renderer,k=this.symbolName,n,z,E=this.shadows,ia=this;if(Ib(a)&&L(b)){c=a;a={};a[c]=b}if(Ib(a)){c=a;ia=c=="strokeWidth"||c=="stroke-width"?
this.strokeweight:this[c]}else for(c in a){d=a[c];n=false;if(k&&/^(x|y|r|start|end|width|height|innerR)/.test(c)){if(!z){this.symbolAttr(a);z=true}n=true}else if(c=="d"){d=d||[];this.d=d.join(" ");e=d.length;for(n=[];e--;)n[e]=bc(d[e])?V(d[e]*10)-5:d[e]=="Z"?"x":d[e];d=n.join(" ")||"x";f.path=d;if(E)for(e=E.length;e--;)E[e].path=d;n=true}else if(c=="zIndex"||c=="visibility"){if(yc&&c=="visibility"&&i=="DIV"){f.gVis=d;n=f.childNodes;for(e=n.length;e--;)La(n[e],{visibility:d});if(d==Ab)d=null}if(d)g[c]=
d;n=true}else if(/^(width|height)$/.test(c)){if(this.updateClipping){this[c]=d;this.updateClipping()}else g[c]=d;n=true}else if(/^(x|y)$/.test(c)){this[c]=d;if(f.tagName=="SPAN")this.updateTransform();else g[{x:"left",y:"top"}[c]]=d}else if(c=="class")f.className=d;else if(c=="stroke"){d=j.color(d,f,c);c="strokecolor"}else if(c=="stroke-width"||c=="strokeWidth"){f.stroked=d?true:false;c="strokeweight";this[c]=d;if(bc(d))d+=Za}else if(c=="dashstyle"){(f.getElementsByTagName("stroke")[0]||eb(j.prepVML(["<stroke/>"]),
null,null,f))[c]=d||"solid";this.dashstyle=d;n=true}else if(c=="fill")if(i=="SPAN")g.color=d;else{f.filled=d!=mb?true:false;d=j.color(d,f,c);c="fillcolor"}else if(c=="translateX"||c=="translateY"||c=="rotation"||c=="align"){if(c=="align")c="textAlign";this[c]=d;this.updateTransform();n=true}else if(c=="text"){f.innerHTML=d;n=true}if(E&&c=="visibility")for(e=E.length;e--;)E[e].style[c]=d;if(!n)if(yc)f[c]=d;else xa(f,c,d)}return ia},clip:function(a){var b=this,c=a.members;c.push(b);b.destroyClip=function(){mc(c,
b)};return b.css(a.getCSS(b.inverted))},css:function(a){var b=this.element;(b=a&&a.width&&b.tagName=="SPAN")&&ma(a,{display:"block",whiteSpace:"normal"});this.styles=ma(this.styles,a);La(this.element,a);b&&this.updateTransform();return this},destroy:function(){this.destroyClip&&this.destroyClip();Hc.prototype.destroy.apply(this)},empty:function(){for(var a=this.element.childNodes,b=a.length,c;b--;){c=a[b];c.parentNode.removeChild(c)}},getBBox:function(){var a=this.element;if(a.nodeName=="text")a.style.position=
lc;return{x:a.offsetLeft,y:a.offsetTop,width:a.offsetWidth,height:a.offsetHeight}},on:function(a,b){this.element["on"+a]=function(){var c=hb.event;c.target=c.srcElement;b(c)};return this},updateTransform:function(){if(this.added){var a=this,b=a.element,c=a.translateX||0,d=a.translateY||0,e=a.x||0,f=a.y||0,g=a.textAlign||"left",i={left:0,center:0.5,right:1}[g],j=g&&g!="left";if(c||d)a.css({marginLeft:c,marginTop:d});a.inverted&&t(b.childNodes,function(A){a.renderer.invertChild(A,b)});if(b.tagName==
"SPAN"){var k,n;c=a.rotation;var z;k=0;d=1;var E=0,ia,T=a.xCorr||0,K=a.yCorr||0,u=[c,g,b.innerHTML,b.style.width].join(",");if(u!=a.cTT){if(L(c)){k=c*Td;d=ub(k);E=yb(k);La(b,{filter:c?["progid:DXImageTransform.Microsoft.Matrix(M11=",d,", M12=",-E,", M21=",E,", M22=",d,", sizingMethod='auto expand')"].join(""):mb})}k=b.offsetWidth;n=b.offsetHeight;z=V(oa(b.style.fontSize||12)*1.2);T=d<0&&-k;K=E<0&&-n;ia=d*E<0;T+=E*z*(ia?1-i:i);K-=d*z*(c?ia?i:1-i:1);if(j){T-=k*i*(d<0?-1:1);if(c)K-=n*i*(E<0?-1:1);La(b,
{textAlign:g})}a.xCorr=T;a.yCorr=K}La(b,{left:e+T,top:f+K});a.cTT=u}}else this.alignOnAdd=true},shadow:function(a){var b=[],c=this.element,d=this.renderer,e,f=c.style,g,i=c.path;if(""+c.path==="")i="x";if(a){for(a=1;a<=3;a++){g=['<shape isShadow="true" strokeweight="',7-2*a,'" filled="false" path="',i,'" coordsize="100,100" style="',c.style.cssText,'" />'];e=eb(d.prepVML(g),null,{left:oa(f.left)+1,top:oa(f.top)+1});g=['<stroke color="black" opacity="',0.05*a,'"/>'];eb(d.prepVML(g),null,null,e);c.parentNode.insertBefore(e,
c);b.push(e)}this.shadows=b}return this}});Ka=function(){this.init.apply(this,arguments)};Ka.prototype=wa(Uc.prototype,{isIE8:wc.indexOf("MSIE 8.0")>-1,init:function(a,b,c){var d;this.Element=fe;this.alignedObjects=[];d=this.createElement(Lb);a.appendChild(d.element);this.box=d.element;this.boxWrapper=d;this.setSize(b,c,false);if(!za.namespaces.hcv){za.namespaces.add("hcv","urn:schemas-microsoft-com:vml");za.createStyleSheet().cssText="hcv\\:fill, hcv\\:path, hcv\\:shape, hcv\\:stroke{ behavior:url(#default#VML); display: inline-block; } "}},
clipRect:function(a,b,c,d){var e=this.createElement();return ma(e,{members:[],left:a,top:b,width:c,height:d,getCSS:function(f){var g=this.top,i=this.left,j=i+this.width,k=g+this.height;g={clip:"rect("+V(f?i:g)+"px,"+V(f?k:j)+"px,"+V(f?j:k)+"px,"+V(f?g:i)+"px)"};!f&&yc&&ma(g,{width:j+Za,height:k+Za});return g},updateClipping:function(){t(e.members,function(f){f.css(e.getCSS(f.inverted))})}})},color:function(a,b,c){var d,e=/^rgba/;if(a&&a.linearGradient){var f,g,i=a.linearGradient,j,k,n,z;t(a.stops,
function(E,ia){if(e.test(E[1])){d=Vb(E[1]);f=d.get("rgb");g=d.get("a")}else{f=E[1];g=1}if(ia){n=f;z=g}else{j=f;k=g}});a=90-Ta.atan((i[3]-i[1])/(i[2]-i[0]))*180/Ub;c=["<",c,' colors="0% ',j,",100% ",n,'" angle="',a,'" opacity="',z,'" o:opacity2="',k,'" type="gradient" focus="100%" />'];eb(this.prepVML(c),null,null,b)}else if(e.test(a)&&b.tagName!="IMG"){d=Vb(a);c=["<",c,' opacity="',d.get("a"),'"/>'];eb(this.prepVML(c),null,null,b);return d.get("rgb")}else return a},prepVML:function(a){var b=this.isIE8;
a=a.join("");if(b){a=a.replace("/>",' xmlns="urn:schemas-microsoft-com:vml" />');a=a.indexOf('style="')==-1?a.replace("/>",' style="display:inline-block;behavior:url(#default#VML);" />'):a.replace('style="','style="display:inline-block;behavior:url(#default#VML);')}else a=a.replace("<","<hcv:");return a},text:function(a,b,c){var d=Ra.chart.style;return this.createElement("span").attr({text:a,x:V(b),y:V(c)}).css({whiteSpace:"nowrap",fontFamily:d.fontFamily,fontSize:d.fontSize})},path:function(a){return this.createElement("shape").attr({coordsize:"100 100",
d:a})},circle:function(a,b,c){return this.path(this.symbols.circle(a,b,c))},g:function(a){var b;if(a)b={className:$b+a,"class":$b+a};return this.createElement(Lb).attr(b)},image:function(a,b,c,d,e){var f=this.createElement("img").attr({src:a});arguments.length>1&&f.css({left:b,top:c,width:d,height:e});return f},rect:function(a,b,c,d,e,f){if(arguments.length>1){var g=(f||0)%2/2;a=V(a||0)+g;b=V(b||0)+g;c=V((c||0)-2*g);d=V((d||0)-2*g)}if(Jb(a)){b=a.y;c=a.width;d=a.height;e=a.r;a=a.x}return this.symbol("rect",
a||0,b||0,e||0,{width:c||0,height:d||0})},invertChild:function(a,b){var c=b.style;La(a,{flip:"x",left:oa(c.width)-10,top:oa(c.height)-10,rotation:-90})},symbols:{arc:function(a,b,c,d){var e=d.start,f=d.end,g=ub(e),i=yb(e),j=ub(f),k=yb(f);d=d.innerR;if(f-e===0)return["x"];else if(f-e==2*Ub)j=-0.07/c;return["wa",a-c,b-c,a+c,b+c,a+c*g,b+c*i,a+c*j,b+c*k,"at",a-d,b-d,a+d,b+d,a+d*j,b+d*k,a+d*g,b+d*i,"x","e"]},circle:function(a,b,c){return["wa",a-c,b-c,a+c,b+c,a+c,b,a+c,b,"e"]},rect:function(a,b,c,d){var e=
d.width;d=d.height;var f=a+e,g=b+d;c=nb(c,e,d);return[Wa,a+c,b,Ba,f-c,b,"wa",f-2*c,b,f,b+2*c,f-c,b,f,b+c,Ba,f,g-c,"wa",f-2*c,g-2*c,f,g,f,g-c,f-c,g,Ba,a+c,g,"wa",a,g-2*c,a+2*c,g,a+c,g,a,g-c,Ba,a,b+c,"wa",a,b,a+2*c,b+2*c,a,b+c,a+c,b,"x","e"]}}})}var Qd=xc?Uc:Ka;Hd.prototype.callbacks=[];var zc=function(){};zc.prototype={init:function(a,b){var c;this.series=a;this.applyOptions(b);this.pointAttr={};if(a.options.colorByPoint){c=a.chart.options.colors;if(!this.options)this.options={};this.color=this.options.color=
this.color||c[Hb++];if(Hb>=c.length)Hb=0}a.chart.pointCount++;return this},applyOptions:function(a){var b=this.series;this.config=a;if(bc(a)||a===null)this.y=a;else if(Jb(a)&&!bc(a.length)){ma(this,a);this.options=a}else if(Ib(a[0])){this.name=a[0];this.y=a[1]}else if(bc(a[0])){this.x=a[0];this.y=a[1]}if(this.x===Qa)this.x=b.autoIncrement()},destroy:function(){var a=this,b=a.series,c;b.chart.pointCount--;a==b.chart.hoverPoint&&a.onMouseOut();b.chart.hoverPoints=null;Bb(a);t(["graphic","tracker","group",
"dataLabel","connector"],function(d){a[d]&&a[d].destroy()});a.legendItem&&a.series.chart.legend.destroyItem(a);for(c in a)a[c]=null},select:function(a,b){var c=this,d=c.series.chart;c.selected=a=y(a,!c.selected);c.firePointEvent(a?"select":"unselect");c.setState(a&&"select");b||t(d.getSelectedPoints(),function(e){if(e.selected&&e!=c){e.selected=false;e.setState(cb);e.firePointEvent("unselect")}})},onMouseOver:function(){var a=this.series.chart,b=a.tooltip,c=a.hoverPoint;c&&c!=this&&c.onMouseOut();
this.firePointEvent("mouseOver");b&&!b.shared&&b.refresh(this);this.setState(xb);a.hoverPoint=this},onMouseOut:function(){this.firePointEvent("mouseOut");this.setState();this.series.chart.hoverPoint=null},tooltipFormatter:function(a){var b=this.series;return['<span style="color:'+b.color+'">',this.name||b.name,"</span>: ",!a?"<b>x = "+(this.name||this.x)+",</b> ":"","<b>",!a?"y = ":"",this.y,"</b><br/>"].join("")},update:function(a,b,c){var d=this,e=d.series,f=e.chart;Kb(c,f);b=y(b,true);d.firePointEvent("update",
{options:a},function(){d.applyOptions(a);e.isDirty=true;b&&f.redraw()})},remove:function(a,b){var c=this,d=c.series,e=d.chart,f=d.data;Kb(b,e);a=y(a,true);c.firePointEvent("remove",null,function(){mc(f,c);c.destroy();d.isDirty=true;a&&e.redraw()})},firePointEvent:function(a,b,c){var d=this,e=this.series.options;if(e.point.events[a]||d.options&&d.options.events&&d.options.events[a])this.importEvents();if(a=="click"&&e.allowPointSelect)c=function(f){d.select(null,f.ctrlKey||f.metaKey||f.shiftKey)};
Ja(this,a,b,c)},importEvents:function(){if(!this.hasImportedEvents){var a=wa(this.series.options.point,this.options).events,b;this.events=a;for(b in a)Pa(this,b,a[b]);this.hasImportedEvents=true}},setState:function(a){var b=this.series,c=b.options.states,d=vb[b.type].marker&&b.options.marker,e=d&&!d.enabled,f=(d=d&&d.states[a])&&d.enabled===false,g=b.stateMarkerGraphic,i=b.chart,j=this.pointAttr;a||(a=cb);if(!(a==this.state||this.selected&&a!="select"||c[a]&&c[a].enabled===false||a&&(f||e&&!d.enabled))){if(this.graphic)this.graphic.attr(j[a]);
else{if(a){if(!g)b.stateMarkerGraphic=g=i.renderer.circle(0,0,j[a].r).attr(j[a]).add(b.group);g.translate(this.plotX,this.plotY)}if(g)g[a?"show":"hide"]()}this.state=a}}};var lb=function(){};lb.prototype={isCartesian:true,type:"line",pointClass:zc,pointAttrToOptions:{stroke:"lineColor","stroke-width":"lineWidth",fill:"fillColor",r:"radius"},init:function(a,b){var c,d;d=a.series.length;this.chart=a;b=this.setOptions(b);ma(this,{index:d,options:b,name:b.name||"Series "+(d+1),state:cb,pointAttr:{},visible:b.visible!==
false,selected:b.selected===true});d=b.events;for(c in d)Pa(this,c,d[c]);if(d&&d.click||b.point&&b.point.events&&b.point.events.click||b.allowPointSelect)a.runTrackerClick=true;this.getColor();this.getSymbol();this.setData(b.data,false)},autoIncrement:function(){var a=this.options,b=this.xIncrement;b=y(b,a.pointStart,0);this.pointInterval=y(this.pointInterval,a.pointInterval,1);this.xIncrement=b+this.pointInterval;return b},cleanData:function(){var a=this.chart,b=this.data,c,d,e=a.smallestInterval,
f,g;b.sort(function(i,j){return i.x-j.x});for(g=b.length-1;g>=0;g--)b[g-1]&&b[g-1].x==b[g].x&&b.splice(g-1,1);for(g=b.length-1;g>=0;g--)if(b[g-1]){f=b[g].x-b[g-1].x;if(d===Qa||f<d){d=f;c=g}}if(e===Qa||d<e)a.smallestInterval=d;this.closestPoints=c},getSegments:function(){var a=-1,b=[],c=this.data;t(c,function(d,e){if(d.y===null){e>a+1&&b.push(c.slice(a+1,e));a=e}else e==c.length-1&&b.push(c.slice(a+1,e+1))});this.segments=b},setOptions:function(a){var b=this.chart.options.plotOptions;return wa(b[this.type],
b.series,a)},getColor:function(){var a=this.chart.options.colors;this.color=this.options.color||a[Hb++]||"#0000ff";if(Hb>=a.length)Hb=0},getSymbol:function(){var a=this.chart.options.symbols;this.symbol=this.options.marker.symbol||a[Wc++];if(Wc>=a.length)Wc=0},addPoint:function(a,b,c,d){var e=this.data,f=this.graph,g=this.area,i=this.chart;a=(new this.pointClass).init(this,a);Kb(d,i);if(f&&c)f.shift=c;if(g){g.shift=c;g.isArea=true}b=y(b,true);e.push(a);c&&e[0].remove(false);this.isDirty=true;b&&i.redraw()},
setData:function(a,b){var c=this,d=c.data,e=c.initialColor,f=c.chart,g=d&&d.length||0;c.xIncrement=null;if(L(e))Hb=e;for(a=jc(nc(a||[]),function(i){return(new c.pointClass).init(c,i)});g--;)d[g].destroy();c.data=a;c.cleanData();c.getSegments();c.isDirty=true;f.isDirtyBox=true;y(b,true)&&f.redraw(false)},remove:function(a,b){var c=this,d=c.chart;a=y(a,true);if(!c.isRemoving){c.isRemoving=true;Ja(c,"remove",null,function(){c.destroy();d.isDirtyLegend=d.isDirtyBox=true;a&&d.redraw(b)})}c.isRemoving=
false},translate:function(){for(var a=this.chart,b=this.options.stacking,c=this.xAxis.categories,d=this.yAxis,e=this.data,f=e.length;f--;){var g=e[f],i=g.x,j=g.y,k=g.low,n=d.stacks[(j<0?"-":"")+this.stackKey];g.plotX=this.xAxis.translate(i);if(b&&this.visible&&n[i]){k=n[i];i=k.total;k.cum=k=k.cum-j;j=k+j;if(b=="percent"){k=i?k*100/i:0;j=i?j*100/i:0}g.percentage=i?g.y*100/i:0;g.stackTotal=i}if(L(k))g.yBottom=d.translate(k,0,1);if(j!==null)g.plotY=d.translate(j,0,1);g.clientX=a.inverted?a.plotHeight-
g.plotX:g.plotX;g.category=c&&c[g.x]!==Qa?c[g.x]:g.x}},setTooltipPoints:function(a){var b=this.chart,c=b.inverted,d=[],e=V((c?b.plotTop:b.plotLeft)+b.plotSizeX),f,g,i=[];if(a)this.tooltipPoints=null;t(this.segments,function(j){d=d.concat(j)});if(this.xAxis&&this.xAxis.reversed)d=d.reverse();t(d,function(j,k){f=d[k-1]?d[k-1].high+1:0;for(g=j.high=d[k+1]?Mb((j.plotX+(d[k+1]?d[k+1].plotX:e))/2):e;f<=g;)i[c?e-f++:f++]=j});this.tooltipPoints=i},onMouseOver:function(){var a=this.chart,b=a.hoverSeries;if(!(!Gb&&
a.mouseIsDown)){b&&b!=this&&b.onMouseOut();this.options.events.mouseOver&&Ja(this,"mouseOver");this.tracker&&this.tracker.toFront();this.setState(xb);a.hoverSeries=this}},onMouseOut:function(){var a=this.options,b=this.chart,c=b.tooltip,d=b.hoverPoint;d&&d.onMouseOut();this&&a.events.mouseOut&&Ja(this,"mouseOut");c&&!a.stickyTracking&&c.hide();this.setState();b.hoverSeries=null},animate:function(a){var b=this.chart,c=this.clipRect,d=this.options.animation;if(d&&!Jb(d))d={};if(a){if(!c.isAnimating){c.attr("width",
0);c.isAnimating=true}}else{c.animate({width:b.plotSizeX},d);this.animate=null}},drawPoints:function(){var a,b=this.data,c=this.chart,d,e,f,g,i,j;if(this.options.marker.enabled)for(f=b.length;f--;){g=b[f];d=g.plotX;e=g.plotY;j=g.graphic;if(e!==Qa&&!isNaN(e)){a=g.pointAttr[g.selected?"select":cb];i=a.r;if(j)j.animate({x:d,y:e,r:i});else g.graphic=c.renderer.symbol(y(g.marker&&g.marker.symbol,this.symbol),d,e,i).attr(a).add(this.group)}}},convertAttribs:function(a,b,c,d){var e=this.pointAttrToOptions,
f,g,i={};a=a||{};b=b||{};c=c||{};d=d||{};for(f in e){g=e[f];i[f]=y(a[g],b[f],c[f],d[f])}return i},getAttribs:function(){var a=this,b=vb[a.type].marker?a.options.marker:a.options,c=b.states,d=c[xb],e,f=a.color,g={stroke:f,fill:f},i=a.data,j=[],k,n=a.pointAttrToOptions;if(a.options.marker){d.radius=d.radius||b.radius+2;d.lineWidth=d.lineWidth||b.lineWidth+1}else d.color=d.color||Vb(d.color||f).brighten(d.brightness).get();j[cb]=a.convertAttribs(b,g);t([xb,"select"],function(E){j[E]=a.convertAttribs(c[E],
j[cb])});a.pointAttr=j;for(f=i.length;f--;){g=i[f];if((b=g.options&&g.options.marker||g.options)&&b.enabled===false)b.radius=0;e=false;if(g.options)for(var z in n)if(L(b[n[z]]))e=true;if(e){k=[];c=b.states||{};e=c[xb]=c[xb]||{};if(!a.options.marker)e.color=Vb(e.color||g.options.color).brighten(e.brightness||d.brightness).get();k[cb]=a.convertAttribs(b,j[cb]);k[xb]=a.convertAttribs(c[xb],j[xb],k[cb]);k.select=a.convertAttribs(c.select,j.select,k[cb])}else k=j;g.pointAttr=k}},destroy:function(){var a=
this,b=a.chart,c=/\/5[0-9\.]+ Safari\//.test(wc),d,e;Bb(a);a.legendItem&&a.chart.legend.destroyItem(a);t(a.data,function(f){f.destroy()});t(["area","graph","dataLabelsGroup","group","tracker"],function(f){if(a[f]){d=c&&f=="group"?"hide":"destroy";a[f][d]()}});if(b.hoverSeries==a)b.hoverSeries=null;mc(b.series,a);for(e in a)delete a[e]},drawDataLabels:function(){if(this.options.dataLabels.enabled){var a=this,b,c,d=a.data,e=a.options.dataLabels,f,g=a.dataLabelsGroup,i=a.chart,j=i.inverted,k=a.type,
n;if(!g)g=a.dataLabelsGroup=i.renderer.g($b+"data-labels").attr({visibility:a.visible?Ab:tb,zIndex:5}).translate(i.plotLeft,i.plotTop).add();n=e.color;if(n=="auto")n=null;e.style.color=y(n,a.color);t(d,function(z){var E=z.barX;E=E&&E+z.barW/2||z.plotX||-999;var ia=y(z.plotY,-999),T=z.dataLabel,K=e.align;f=e.formatter.call({x:z.x,y:z.y,series:a,point:z,percentage:z.percentage,total:z.total||z.stackTotal});b=(j?i.plotWidth-ia:E)+e.x;c=(j?i.plotHeight-E:ia)+e.y;if(k=="column")b+={left:-1,right:1}[K]*
z.barW/2||0;if(T)T.animate({x:b,y:c});else if(f)T=z.dataLabel=i.renderer.text(f,b,c).attr({align:K,rotation:e.rotation,zIndex:1}).css(e.style).add(g);j&&!e.y&&T.attr({y:c+parseInt(T.styles.lineHeight)*0.9-T.getBBox().height/2})})}},drawGraph:function(){var a=this,b=a.options,c=a.graph,d=[],e,f=a.area,g=a.group,i=b.lineColor||a.color,j=b.lineWidth,k=b.dashStyle,n,z=a.chart.renderer,E=a.yAxis.getThreshold(b.threshold||0),ia=/^area/.test(a.type),T=[],K=[];t(a.segments,function(u){n=[];t(u,function(ea,
qa){if(a.getPointSpline)n.push.apply(n,a.getPointSpline(u,ea,qa));else{n.push(qa?Ba:Wa);qa&&b.step&&n.push(ea.plotX,u[qa-1].plotY);n.push(ea.plotX,ea.plotY)}});if(u.length>1)d=d.concat(n);else T.push(u[0]);if(ia){var A=[],ba,ya=n.length;for(ba=0;ba<ya;ba++)A.push(n[ba]);ya==3&&A.push(Ba,n[1],n[2]);if(b.stacking&&a.type!="areaspline")for(ba=u.length-1;ba>=0;ba--)A.push(u[ba].plotX,u[ba].yBottom);else A.push(Ba,u[u.length-1].plotX,E,Ba,u[0].plotX,E);K=K.concat(A)}});a.graphPath=d;a.singlePoints=T;if(ia){e=
y(b.fillColor,Vb(a.color).setOpacity(b.fillOpacity||0.75).get());if(f)f.animate({d:K});else a.area=a.chart.renderer.path(K).attr({fill:e}).add(g)}if(c)c.animate({d:d});else if(j){c={stroke:i,"stroke-width":j};if(k)c.dashstyle=k;a.graph=z.path(d).attr(c).add(g).shadow(b.shadow)}},render:function(){var a=this,b=a.chart,c,d,e=a.options,f=e.animation,g=f&&a.animate;f=g?f&&f.duration||500:0;var i=a.clipRect;d=b.renderer;if(!i){i=a.clipRect=!b.hasRendered&&b.clipRect?b.clipRect:d.clipRect(0,0,b.plotSizeX,
b.plotSizeY);if(!b.clipRect)b.clipRect=i}if(!a.group){c=a.group=d.g("series");if(b.inverted){d=function(){c.attr({width:b.plotWidth,height:b.plotHeight}).invert()};d();Pa(b,"resize",d)}c.clip(a.clipRect).attr({visibility:a.visible?Ab:tb,zIndex:e.zIndex}).translate(b.plotLeft,b.plotTop).add(b.seriesGroup)}a.drawDataLabels();g&&a.animate(true);a.getAttribs();a.drawGraph&&a.drawGraph();a.drawPoints();a.options.enableMouseTracking!==false&&a.drawTracker();g&&a.animate();setTimeout(function(){i.isAnimating=
false;if((c=a.group)&&i!=b.clipRect&&i.renderer){c.clip(a.clipRect=b.clipRect);i.destroy()}},f);a.isDirty=false},redraw:function(){var a=this.chart,b=this.group;if(b){a.inverted&&b.attr({width:a.plotWidth,height:a.plotHeight});b.animate({translateX:a.plotLeft,translateY:a.plotTop})}this.translate();this.setTooltipPoints(true);this.render()},setState:function(a){var b=this.options,c=this.graph,d=b.states;b=b.lineWidth;a=a||cb;if(this.state!=a){this.state=a;if(!(d[a]&&d[a].enabled===false)){if(a)b=
d[a].lineWidth||b+1;if(c&&!c.dashstyle)c.attr({"stroke-width":b},a?0:500)}}},setVisible:function(a,b){var c=this.chart,d=this.legendItem,e=this.group,f=this.tracker,g=this.dataLabelsGroup,i,j=this.data,k=c.options.chart.ignoreHiddenSeries;i=this.visible;i=(this.visible=a=a===Qa?!i:a)?"show":"hide";e&&e[i]();if(f)f[i]();else for(e=j.length;e--;){f=j[e];f.tracker&&f.tracker[i]()}g&&g[i]();d&&c.legend.colorizeItem(this,a);this.isDirty=true;this.options.stacking&&t(c.series,function(n){if(n.options.stacking&&
n.visible)n.isDirty=true});if(k)c.isDirtyBox=true;b!==false&&c.redraw();Ja(this,i)},show:function(){this.setVisible(true)},hide:function(){this.setVisible(false)},select:function(a){this.selected=a=a===Qa?!this.selected:a;if(this.checkbox)this.checkbox.checked=a;Ja(this,a?"select":"unselect")},drawTracker:function(){var a=this,b=a.options,c=[].concat(a.graphPath),d=c.length,e=a.chart,f=e.options.tooltip.snap,g=a.tracker,i=b.cursor;i=i&&{cursor:i};var j=a.singlePoints,k;if(d)for(k=d+1;k--;){c[k]==
Wa&&c.splice(k+1,0,c[k+1]-f,c[k+2],Ba);if(k&&c[k]==Wa||k==d)c.splice(k,0,Ba,c[k-2]+f,c[k-1])}for(k=0;k<j.length;k++){d=j[k];c.push(Wa,d.plotX-f,d.plotY,Ba,d.plotX+f,d.plotY)}if(g)g.attr({d:c});else a.tracker=e.renderer.path(c).attr({isTracker:true,stroke:Ud,fill:mb,"stroke-width":b.lineWidth+2*f,visibility:a.visible?Ab:tb,zIndex:1}).on(Gb?"touchstart":"mouseover",function(){e.hoverSeries!=a&&a.onMouseOver()}).on("mouseout",function(){b.stickyTracking||a.onMouseOut()}).css(i).add(e.trackerGroup)}};
Ka=wb(lb);sb.line=Ka;Ka=wb(lb,{type:"area"});sb.area=Ka;Ka=wb(lb,{type:"spline",getPointSpline:function(a,b,c){var d=b.plotX,e=b.plotY,f=a[c-1],g=a[c+1],i,j,k,n;if(c&&c<a.length-1){a=f.plotY;k=g.plotX;g=g.plotY;var z;i=(1.5*d+f.plotX)/2.5;j=(1.5*e+a)/2.5;k=(1.5*d+k)/2.5;n=(1.5*e+g)/2.5;z=(n-j)*(k-d)/(k-i)+e-n;j+=z;n+=z;if(j>a&&j>e){j=Ga(a,e);n=2*e-j}else if(j<a&&j<e){j=nb(a,e);n=2*e-j}if(n>g&&n>e){n=Ga(g,e);j=2*e-n}else if(n<g&&n<e){n=nb(g,e);j=2*e-n}b.rightContX=k;b.rightContY=n}if(c){b=["C",f.rightContX||
f.plotX,f.rightContY||f.plotY,i||d,j||e,d,e];f.rightContX=f.rightContY=null}else b=[Wa,d,e];return b}});sb.spline=Ka;Ka=wb(Ka,{type:"areaspline"});sb.areaspline=Ka;var Zc=wb(lb,{type:"column",pointAttrToOptions:{stroke:"borderColor","stroke-width":"borderWidth",fill:"color",r:"borderRadius"},init:function(){lb.prototype.init.apply(this,arguments);var a=this,b=a.chart;b.hasColumn=true;b.hasRendered&&t(b.series,function(c){if(c.type==a.type)c.isDirty=true})},translate:function(){var a=this,b=a.chart,
c=0,d=a.xAxis.reversed,e=a.xAxis.categories,f={},g,i;lb.prototype.translate.apply(a);t(b.series,function(A){if(A.type==a.type){if(A.options.stacking){g=A.stackKey;if(f[g]===Qa)f[g]=c++;i=f[g]}else i=c++;A.columnIndex=i}});var j=a.options,k=a.data,n=a.closestPoints;b=ab(k[1]?k[n].plotX-k[n-1].plotX:b.plotSizeX/(e?e.length:1));e=b*j.groupPadding;n=(b-2*e)/c;var z=j.pointWidth,E=L(z)?(n-z)/2:n*j.pointPadding,ia=y(z,n-2*E),T=E+(e+((d?c-a.columnIndex:a.columnIndex)||0)*n-b/2)*(d?-1:1),K=a.yAxis.getThreshold(j.threshold||
0),u=y(j.minPointLength,5);t(k,function(A){var ba=A.plotY,ya=A.yBottom||K,ea=A.plotX+T,qa=dd(nb(ba,ya)),$a=dd(Ga(ba,ya)-qa),jb;if(ab($a)<u){if(u){$a=u;qa=ab(qa-K)>u?ya-u:K-(ba<=K?u:0)}jb=qa-3}ma(A,{barX:ea,barY:qa,barW:ia,barH:$a});A.shapeType="rect";A.shapeArgs={x:ea,y:qa,width:ia,height:$a,r:j.borderRadius};A.trackerArgs=L(jb)&&wa(A.shapeArgs,{height:Ga(6,$a+3),y:jb})})},getSymbol:function(){},drawGraph:function(){},drawPoints:function(){var a=this,b=a.options,c=a.chart.renderer,d,e;t(a.data,function(f){var g=
f.plotY;if(g!==Qa&&!isNaN(g)){d=f.graphic;e=f.shapeArgs;if(d){Sc(d);d.animate(e)}else f.graphic=c[f.shapeType](e).attr(f.pointAttr[f.selected?"select":cb]).add(a.group).shadow(b.shadow)}})},drawTracker:function(){var a=this,b=a.chart,c=b.renderer,d,e,f=+new Date,g=a.options.cursor,i=g&&{cursor:g},j;t(a.data,function(k){e=k.tracker;d=k.trackerArgs||k.shapeArgs;if(k.y!==null)if(e)e.attr(d);else k.tracker=c[k.shapeType](d).attr({isTracker:f,fill:Ud,visibility:a.visible?Ab:tb,zIndex:1}).on(Gb?"touchstart":
"mouseover",function(n){j=n.relatedTarget||n.fromElement;b.hoverSeries!=a&&xa(j,"isTracker")!=f&&a.onMouseOver();k.onMouseOver()}).on("mouseout",function(n){if(!a.options.stickyTracking){j=n.relatedTarget||n.toElement;xa(j,"isTracker")!=f&&a.onMouseOut()}}).css(i).add(b.trackerGroup)})},animate:function(a){var b=this,c=b.data;if(!a){t(c,function(d){var e=d.graphic;if(e){e.attr({height:0,y:b.yAxis.translate(0,0,1)});e.animate({height:d.barH,y:d.barY},b.options.animation)}});b.animate=null}},remove:function(){var a=
this,b=a.chart;b.hasRendered&&t(b.series,function(c){if(c.type==a.type)c.isDirty=true});lb.prototype.remove.apply(a,arguments)}});sb.column=Zc;Ka=wb(Zc,{type:"bar",init:function(a){a.inverted=this.inverted=true;Zc.prototype.init.apply(this,arguments)}});sb.bar=Ka;Ka=wb(lb,{type:"scatter",translate:function(){var a=this;lb.prototype.translate.apply(a);t(a.data,function(b){b.shapeType="circle";b.shapeArgs={x:b.plotX,y:b.plotY,r:a.chart.options.tooltip.snap}})},drawTracker:function(){var a=this,b=a.options.cursor,
c=b&&{cursor:b},d;t(a.data,function(e){(d=e.graphic)&&d.attr({isTracker:true}).on("mouseover",function(){a.onMouseOver();e.onMouseOver()}).on("mouseout",function(){a.options.stickyTracking||a.onMouseOut()}).css(c)})},cleanData:function(){}});sb.scatter=Ka;Ka=wb(zc,{init:function(){zc.prototype.init.apply(this,arguments);var a=this,b;ma(a,{visible:a.visible!==false,name:y(a.name,"Slice")});b=function(){a.slice()};Pa(a,"select",b);Pa(a,"unselect",b);return a},setVisible:function(a){var b=this.series.chart,
c=this.tracker,d=this.dataLabel,e=this.connector,f;f=(this.visible=a=a===Qa?!this.visible:a)?"show":"hide";this.group[f]();c&&c[f]();d&&d[f]();e&&e[f]();this.legendItem&&b.legend.colorizeItem(this,a)},slice:function(a,b,c){var d=this.series.chart,e=this.slicedTranslation;Kb(c,d);y(b,true);a=this.sliced=L(a)?a:!this.sliced;this.group.animate({translateX:a?e[0]:d.plotLeft,translateY:a?e[1]:d.plotTop})}});Ka=wb(lb,{type:"pie",isCartesian:false,pointClass:Ka,pointAttrToOptions:{stroke:"borderColor","stroke-width":"borderWidth",
fill:"color"},getColor:function(){this.initialColor=Hb},animate:function(){var a=this;t(a.data,function(b){var c=b.graphic;b=b.shapeArgs;var d=-Ub/2;if(c){c.attr({r:0,start:d,end:d});c.animate({r:b.r,start:b.start,end:b.end},a.options.animation)}});a.animate=null},translate:function(){var a=0,b=-0.25,c=this.options,d=c.slicedOffset,e=d+c.borderWidth,f=c.center,g=this.chart,i=g.plotWidth,j=g.plotHeight,k,n,z,E=this.data,ia=2*Ub,T,K=nb(i,j),u,A,ba,ya=c.dataLabels.distance;f.push(c.size,c.innerSize||
0);f=jc(f,function(ea,qa){return(u=/%$/.test(ea))?[i,j,K,K][qa]*oa(ea)/100:ea});this.getX=function(ea,qa){z=Ta.asin((ea-f[1])/(f[2]/2+ya));return f[0]+(qa?-1:1)*ub(z)*(f[2]/2+ya)};this.center=f;t(E,function(ea){a+=ea.y});t(E,function(ea){T=a?ea.y/a:0;k=V(b*ia*1E3)/1E3;b+=T;n=V(b*ia*1E3)/1E3;ea.shapeType="arc";ea.shapeArgs={x:f[0],y:f[1],r:f[2]/2,innerR:f[3]/2,start:k,end:n};z=(n+k)/2;ea.slicedTranslation=jc([ub(z)*d+g.plotLeft,yb(z)*d+g.plotTop],V);A=ub(z)*f[2]/2;ba=yb(z)*f[2]/2;ea.tooltipPos=[f[0]+
A*0.7,f[1]+ba*0.7];ea.labelPos=[f[0]+A+ub(z)*ya,f[1]+ba+yb(z)*ya,f[0]+A+ub(z)*e,f[1]+ba+yb(z)*e,f[0]+A,f[1]+ba,ya<0?"center":z<ia/4?"left":"right",z];ea.percentage=T*100;ea.total=a});this.setTooltipPoints()},render:function(){this.getAttribs();this.drawPoints();this.options.enableMouseTracking!==false&&this.drawTracker();this.drawDataLabels();this.options.animation&&this.animate&&this.animate();this.isDirty=false},drawPoints:function(){var a=this.chart,b=a.renderer,c,d,e,f;t(this.data,function(g){d=
g.graphic;f=g.shapeArgs;e=g.group;if(!e)e=g.group=b.g("point").attr({zIndex:5}).add();c=g.sliced?g.slicedTranslation:[a.plotLeft,a.plotTop];e.translate(c[0],c[1]);if(d)d.animate(f);else g.graphic=b.arc(f).attr(ma(g.pointAttr[cb],{"stroke-linejoin":"round"})).add(g.group);g.visible===false&&g.setVisible(false)})},drawDataLabels:function(){var a=this.data,b,c=this.chart,d=this.options.dataLabels,e=y(d.connectorPadding,10),f=y(d.connectorWidth,1),g,i,j=d.distance>0,k,n,z=this.center[1],E=[[],[],[],[]],
ia,T,K,u,A,ba,ya,ea=4,qa;lb.prototype.drawDataLabels.apply(this);t(a,function($a){var jb=$a.labelPos[7];E[jb<0?0:jb<Ub/2?1:jb<Ub?2:3].push($a)});E[1].reverse();E[3].reverse();for(ya=function($a,jb){return $a.y>jb.y};ea--;){a=0;b=[].concat(E[ea]);b.sort(ya);for(qa=b.length;qa--;)b[qa].rank=qa;for(u=0;u<2;u++){n=(ba=ea%3)?9999:-9999;A=ba?-1:1;for(qa=0;qa<E[ea].length;qa++){b=E[ea][qa];if(g=b.dataLabel){i=b.labelPos;K=Ab;ia=i[0];T=i[1];k||(k=g&&g.getBBox().height);if(j)if(u&&b.rank<a)K=tb;else if(!ba&&
T<n+k||ba&&T>n-k){T=n+A*k;ia=this.getX(T,ea>1);if(!ba&&T+k>z||ba&&T-k<z)if(u)K=tb;else a++}if(b.visible===false)K=tb;if(K==Ab)n=T;if(u){g.attr({visibility:K,align:i[6]})[g.moved?"animate":"attr"]({x:ia+d.x+({left:e,right:-e}[i[6]]||0),y:T+d.y});g.moved=true;if(j&&f){g=b.connector;i=[Wa,ia+(i[6]=="left"?5:-5),T,Ba,ia,T,Ba,i[2],i[3],Ba,i[4],i[5]];if(g){g.animate({d:i});g.attr("visibility",K)}else b.connector=g=this.chart.renderer.path(i).attr({"stroke-width":f,stroke:d.connectorColor||"#606060",visibility:K,
zIndex:3}).translate(c.plotLeft,c.plotTop).add()}}}}}}},drawTracker:Zc.prototype.drawTracker,getSymbol:function(){}});sb.pie=Ka;hb.Highcharts={Chart:Hd,dateFormat:Mc,pathAnim:Yc,getOptions:function(){return Ra},numberFormat:Gd,Point:zc,Color:Vb,Renderer:Qd,seriesTypes:sb,setOptions:function(a){Ra=wa(Ra,a);Bd();return Ra},Series:lb,addEvent:Pa,createElement:eb,discardElement:Fc,css:La,each:t,extend:ma,map:jc,merge:wa,pick:y,extendClass:wb,version:"2.1.2"}})();

/*jslint browser: true */ /*global jQuery: true */

/**
 * jQuery Cookie plugin
 *
 * Copyright (c) 2010 Klaus Hartl (stilbuero.de)
 * Dual licensed under the MIT and GPL licenses:
 * http://www.opensource.org/licenses/mit-license.php
 * http://www.gnu.org/licenses/gpl.html
 *
 */

// TODO JsDoc

/**
 * Create a cookie with the given key and value and other optional parameters.
 *
 * @example $.cookie('the_cookie', 'the_value');
 * @desc Set the value of a cookie.
 * @example $.cookie('the_cookie', 'the_value', { expires: 7, path: '/', domain: 'jquery.com', secure: true });
 * @desc Create a cookie with all available options.
 * @example $.cookie('the_cookie', 'the_value');
 * @desc Create a session cookie.
 * @example $.cookie('the_cookie', null);
 * @desc Delete a cookie by passing null as value. Keep in mind that you have to use the same path and domain
 *       used when the cookie was set.
 *
 * @param String key The key of the cookie.
 * @param String value The value of the cookie.
 * @param Object options An object literal containing key/value pairs to provide optional cookie attributes.
 * @option Number|Date expires Either an integer specifying the expiration date from now on in days or a Date object.
 *                             If a negative value is specified (e.g. a date in the past), the cookie will be deleted.
 *                             If set to null or omitted, the cookie will be a session cookie and will not be retained
 *                             when the the browser exits.
 * @option String path The value of the path atribute of the cookie (default: path of page that created the cookie).
 * @option String domain The value of the domain attribute of the cookie (default: domain of page that created the cookie).
 * @option Boolean secure If true, the secure attribute of the cookie will be set and the cookie transmission will
 *                        require a secure protocol (like HTTPS).
 * @type undefined
 *
 * @name $.cookie
 * @cat Plugins/Cookie
 * @author Klaus Hartl/klaus.hartl@stilbuero.de
 */

/**
 * Get the value of a cookie with the given key.
 *
 * @example $.cookie('the_cookie');
 * @desc Get the value of a cookie.
 *
 * @param String key The key of the cookie.
 * @return The value of the cookie.
 * @type String
 *
 * @name $.cookie
 * @cat Plugins/Cookie
 * @author Klaus Hartl/klaus.hartl@stilbuero.de
 */
jQuery.cookie = function (key, value, options) {

    // key and value given, set cookie...
    if (arguments.length > 1 && (value === null || typeof value !== "object")) {
        options = jQuery.extend({}, options);

        if (value === null) {
            options.expires = -1;
        }

        if (typeof options.expires === 'number') {
            var days = options.expires, t = options.expires = new Date();
            t.setDate(t.getDate() + days);
        }

        return (document.cookie = [
            encodeURIComponent(key), '=',
            options.raw ? String(value) : encodeURIComponent(String(value)),
            options.expires ? '; expires=' + options.expires.toUTCString() : '', // use expires attribute, max-age is not supported by IE
            options.path ? '; path=' + options.path : '',
            options.domain ? '; domain=' + options.domain : '',
            options.secure ? '; secure' : ''
        ].join(''));
    }

    // key and possibly options given, get cookie...
    options = value || {};
    var result, decode = options.raw ? function (s) { return s; } : decodeURIComponent;
    return (result = new RegExp('(?:^|; )' + encodeURIComponent(key) + '=([^;]*)').exec(document.cookie)) ? decode(result[1]) : null;
};

/*
 * File:        jquery.dataTables.min.js
 * Version:     1.8.2
 * Author:      Allan Jardine (www.sprymedia.co.uk)
 * Info:        www.datatables.net
 * 
 * Copyright 2008-2010 Allan Jardine, all rights reserved.
 *
 * This source file is free software, under either the GPL v2 license or a
 * BSD style license, available at:
 *   http://datatables.net/license_gpl2
 *   http://datatables.net/license_bsd
 * 
 * This source file is distributed in the hope that it will be useful, but 
 * WITHOUT ANY WARRANTY; without even the implied warranty of MERCHANTABILITY 
 * or FITNESS FOR A PARTICULAR PURPOSE. See the license files for details.
 */
(function(i,za,p){i.fn.dataTableSettings=[];var D=i.fn.dataTableSettings;i.fn.dataTableExt={};var n=i.fn.dataTableExt;n.sVersion="1.8.2";n.sErrMode="alert";n.iApiIndex=0;n.oApi={};n.afnFiltering=[];n.aoFeatures=[];n.ofnSearch={};n.afnSortData=[];n.oStdClasses={sPagePrevEnabled:"paginate_enabled_previous",sPagePrevDisabled:"paginate_disabled_previous",sPageNextEnabled:"paginate_enabled_next",sPageNextDisabled:"paginate_disabled_next",sPageJUINext:"",sPageJUIPrev:"",sPageButton:"paginate_button",sPageButtonActive:"paginate_active",
sPageButtonStaticDisabled:"paginate_button paginate_button_disabled",sPageFirst:"first",sPagePrevious:"previous",sPageNext:"next",sPageLast:"last",sStripeOdd:"odd",sStripeEven:"even",sRowEmpty:"dataTables_empty",sWrapper:"dataTables_wrapper",sFilter:"dataTables_filter",sInfo:"dataTables_info",sPaging:"dataTables_paginate paging_",sLength:"dataTables_length",sProcessing:"dataTables_processing",sSortAsc:"sorting_asc",sSortDesc:"sorting_desc",sSortable:"sorting",sSortableAsc:"sorting_asc_disabled",sSortableDesc:"sorting_desc_disabled",
sSortableNone:"sorting_disabled",sSortColumn:"sorting_",sSortJUIAsc:"",sSortJUIDesc:"",sSortJUI:"",sSortJUIAscAllowed:"",sSortJUIDescAllowed:"",sSortJUIWrapper:"",sSortIcon:"",sScrollWrapper:"dataTables_scroll",sScrollHead:"dataTables_scrollHead",sScrollHeadInner:"dataTables_scrollHeadInner",sScrollBody:"dataTables_scrollBody",sScrollFoot:"dataTables_scrollFoot",sScrollFootInner:"dataTables_scrollFootInner",sFooterTH:""};n.oJUIClasses={sPagePrevEnabled:"fg-button ui-button ui-state-default ui-corner-left",
sPagePrevDisabled:"fg-button ui-button ui-state-default ui-corner-left ui-state-disabled",sPageNextEnabled:"fg-button ui-button ui-state-default ui-corner-right",sPageNextDisabled:"fg-button ui-button ui-state-default ui-corner-right ui-state-disabled",sPageJUINext:"ui-icon ui-icon-circle-arrow-e",sPageJUIPrev:"ui-icon ui-icon-circle-arrow-w",sPageButton:"fg-button ui-button ui-state-default",sPageButtonActive:"fg-button ui-button ui-state-default ui-state-disabled",sPageButtonStaticDisabled:"fg-button ui-button ui-state-default ui-state-disabled",
sPageFirst:"first ui-corner-tl ui-corner-bl",sPagePrevious:"previous",sPageNext:"next",sPageLast:"last ui-corner-tr ui-corner-br",sStripeOdd:"odd",sStripeEven:"even",sRowEmpty:"dataTables_empty",sWrapper:"dataTables_wrapper",sFilter:"dataTables_filter",sInfo:"dataTables_info",sPaging:"dataTables_paginate fg-buttonset ui-buttonset fg-buttonset-multi ui-buttonset-multi paging_",sLength:"dataTables_length",sProcessing:"dataTables_processing",sSortAsc:"ui-state-default",sSortDesc:"ui-state-default",sSortable:"ui-state-default",
sSortableAsc:"ui-state-default",sSortableDesc:"ui-state-default",sSortableNone:"ui-state-default",sSortColumn:"sorting_",sSortJUIAsc:"css_right ui-icon ui-icon-triangle-1-n",sSortJUIDesc:"css_right ui-icon ui-icon-triangle-1-s",sSortJUI:"css_right ui-icon ui-icon-carat-2-n-s",sSortJUIAscAllowed:"css_right ui-icon ui-icon-carat-1-n",sSortJUIDescAllowed:"css_right ui-icon ui-icon-carat-1-s",sSortJUIWrapper:"DataTables_sort_wrapper",sSortIcon:"DataTables_sort_icon",sScrollWrapper:"dataTables_scroll",
sScrollHead:"dataTables_scrollHead ui-state-default",sScrollHeadInner:"dataTables_scrollHeadInner",sScrollBody:"dataTables_scrollBody",sScrollFoot:"dataTables_scrollFoot ui-state-default",sScrollFootInner:"dataTables_scrollFootInner",sFooterTH:"ui-state-default"};n.oPagination={two_button:{fnInit:function(g,l,s){var t,w,y;if(g.bJUI){t=p.createElement("a");w=p.createElement("a");y=p.createElement("span");y.className=g.oClasses.sPageJUINext;w.appendChild(y);y=p.createElement("span");y.className=g.oClasses.sPageJUIPrev;
t.appendChild(y)}else{t=p.createElement("div");w=p.createElement("div")}t.className=g.oClasses.sPagePrevDisabled;w.className=g.oClasses.sPageNextDisabled;t.title=g.oLanguage.oPaginate.sPrevious;w.title=g.oLanguage.oPaginate.sNext;l.appendChild(t);l.appendChild(w);i(t).bind("click.DT",function(){g.oApi._fnPageChange(g,"previous")&&s(g)});i(w).bind("click.DT",function(){g.oApi._fnPageChange(g,"next")&&s(g)});i(t).bind("selectstart.DT",function(){return false});i(w).bind("selectstart.DT",function(){return false});
if(g.sTableId!==""&&typeof g.aanFeatures.p=="undefined"){l.setAttribute("id",g.sTableId+"_paginate");t.setAttribute("id",g.sTableId+"_previous");w.setAttribute("id",g.sTableId+"_next")}},fnUpdate:function(g){if(g.aanFeatures.p)for(var l=g.aanFeatures.p,s=0,t=l.length;s<t;s++)if(l[s].childNodes.length!==0){l[s].childNodes[0].className=g._iDisplayStart===0?g.oClasses.sPagePrevDisabled:g.oClasses.sPagePrevEnabled;l[s].childNodes[1].className=g.fnDisplayEnd()==g.fnRecordsDisplay()?g.oClasses.sPageNextDisabled:
g.oClasses.sPageNextEnabled}}},iFullNumbersShowPages:5,full_numbers:{fnInit:function(g,l,s){var t=p.createElement("span"),w=p.createElement("span"),y=p.createElement("span"),F=p.createElement("span"),x=p.createElement("span");t.innerHTML=g.oLanguage.oPaginate.sFirst;w.innerHTML=g.oLanguage.oPaginate.sPrevious;F.innerHTML=g.oLanguage.oPaginate.sNext;x.innerHTML=g.oLanguage.oPaginate.sLast;var v=g.oClasses;t.className=v.sPageButton+" "+v.sPageFirst;w.className=v.sPageButton+" "+v.sPagePrevious;F.className=
v.sPageButton+" "+v.sPageNext;x.className=v.sPageButton+" "+v.sPageLast;l.appendChild(t);l.appendChild(w);l.appendChild(y);l.appendChild(F);l.appendChild(x);i(t).bind("click.DT",function(){g.oApi._fnPageChange(g,"first")&&s(g)});i(w).bind("click.DT",function(){g.oApi._fnPageChange(g,"previous")&&s(g)});i(F).bind("click.DT",function(){g.oApi._fnPageChange(g,"next")&&s(g)});i(x).bind("click.DT",function(){g.oApi._fnPageChange(g,"last")&&s(g)});i("span",l).bind("mousedown.DT",function(){return false}).bind("selectstart.DT",
function(){return false});if(g.sTableId!==""&&typeof g.aanFeatures.p=="undefined"){l.setAttribute("id",g.sTableId+"_paginate");t.setAttribute("id",g.sTableId+"_first");w.setAttribute("id",g.sTableId+"_previous");F.setAttribute("id",g.sTableId+"_next");x.setAttribute("id",g.sTableId+"_last")}},fnUpdate:function(g,l){if(g.aanFeatures.p){var s=n.oPagination.iFullNumbersShowPages,t=Math.floor(s/2),w=Math.ceil(g.fnRecordsDisplay()/g._iDisplayLength),y=Math.ceil(g._iDisplayStart/g._iDisplayLength)+1,F=
"",x,v=g.oClasses;if(w<s){t=1;x=w}else if(y<=t){t=1;x=s}else if(y>=w-t){t=w-s+1;x=w}else{t=y-Math.ceil(s/2)+1;x=t+s-1}for(s=t;s<=x;s++)F+=y!=s?'<span class="'+v.sPageButton+'">'+s+"</span>":'<span class="'+v.sPageButtonActive+'">'+s+"</span>";x=g.aanFeatures.p;var z,$=function(M){g._iDisplayStart=(this.innerHTML*1-1)*g._iDisplayLength;l(g);M.preventDefault()},X=function(){return false};s=0;for(t=x.length;s<t;s++)if(x[s].childNodes.length!==0){z=i("span:eq(2)",x[s]);z.html(F);i("span",z).bind("click.DT",
$).bind("mousedown.DT",X).bind("selectstart.DT",X);z=x[s].getElementsByTagName("span");z=[z[0],z[1],z[z.length-2],z[z.length-1]];i(z).removeClass(v.sPageButton+" "+v.sPageButtonActive+" "+v.sPageButtonStaticDisabled);if(y==1){z[0].className+=" "+v.sPageButtonStaticDisabled;z[1].className+=" "+v.sPageButtonStaticDisabled}else{z[0].className+=" "+v.sPageButton;z[1].className+=" "+v.sPageButton}if(w===0||y==w||g._iDisplayLength==-1){z[2].className+=" "+v.sPageButtonStaticDisabled;z[3].className+=" "+
v.sPageButtonStaticDisabled}else{z[2].className+=" "+v.sPageButton;z[3].className+=" "+v.sPageButton}}}}}};n.oSort={"string-asc":function(g,l){if(typeof g!="string")g="";if(typeof l!="string")l="";g=g.toLowerCase();l=l.toLowerCase();return g<l?-1:g>l?1:0},"string-desc":function(g,l){if(typeof g!="string")g="";if(typeof l!="string")l="";g=g.toLowerCase();l=l.toLowerCase();return g<l?1:g>l?-1:0},"html-asc":function(g,l){g=g.replace(/<.*?>/g,"").toLowerCase();l=l.replace(/<.*?>/g,"").toLowerCase();return g<
l?-1:g>l?1:0},"html-desc":function(g,l){g=g.replace(/<.*?>/g,"").toLowerCase();l=l.replace(/<.*?>/g,"").toLowerCase();return g<l?1:g>l?-1:0},"date-asc":function(g,l){g=Date.parse(g);l=Date.parse(l);if(isNaN(g)||g==="")g=Date.parse("01/01/1970 00:00:00");if(isNaN(l)||l==="")l=Date.parse("01/01/1970 00:00:00");return g-l},"date-desc":function(g,l){g=Date.parse(g);l=Date.parse(l);if(isNaN(g)||g==="")g=Date.parse("01/01/1970 00:00:00");if(isNaN(l)||l==="")l=Date.parse("01/01/1970 00:00:00");return l-
g},"numeric-asc":function(g,l){return(g=="-"||g===""?0:g*1)-(l=="-"||l===""?0:l*1)},"numeric-desc":function(g,l){return(l=="-"||l===""?0:l*1)-(g=="-"||g===""?0:g*1)}};n.aTypes=[function(g){if(typeof g=="number")return"numeric";else if(typeof g!="string")return null;var l,s=false;l=g.charAt(0);if("0123456789-".indexOf(l)==-1)return null;for(var t=1;t<g.length;t++){l=g.charAt(t);if("0123456789.".indexOf(l)==-1)return null;if(l=="."){if(s)return null;s=true}}return"numeric"},function(g){var l=Date.parse(g);
if(l!==null&&!isNaN(l)||typeof g=="string"&&g.length===0)return"date";return null},function(g){if(typeof g=="string"&&g.indexOf("<")!=-1&&g.indexOf(">")!=-1)return"html";return null}];n.fnVersionCheck=function(g){var l=function(x,v){for(;x.length<v;)x+="0";return x},s=n.sVersion.split(".");g=g.split(".");for(var t="",w="",y=0,F=g.length;y<F;y++){t+=l(s[y],3);w+=l(g[y],3)}return parseInt(t,10)>=parseInt(w,10)};n._oExternConfig={iNextUnique:0};i.fn.dataTable=function(g){function l(){this.fnRecordsTotal=
function(){return this.oFeatures.bServerSide?parseInt(this._iRecordsTotal,10):this.aiDisplayMaster.length};this.fnRecordsDisplay=function(){return this.oFeatures.bServerSide?parseInt(this._iRecordsDisplay,10):this.aiDisplay.length};this.fnDisplayEnd=function(){return this.oFeatures.bServerSide?this.oFeatures.bPaginate===false||this._iDisplayLength==-1?this._iDisplayStart+this.aiDisplay.length:Math.min(this._iDisplayStart+this._iDisplayLength,this._iRecordsDisplay):this._iDisplayEnd};this.sInstance=
this.oInstance=null;this.oFeatures={bPaginate:true,bLengthChange:true,bFilter:true,bSort:true,bInfo:true,bAutoWidth:true,bProcessing:false,bSortClasses:true,bStateSave:false,bServerSide:false,bDeferRender:false};this.oScroll={sX:"",sXInner:"",sY:"",bCollapse:false,bInfinite:false,iLoadGap:100,iBarWidth:0,bAutoCss:true};this.aanFeatures=[];this.oLanguage={sProcessing:"Processing...",sLengthMenu:"Show _MENU_ entries",sZeroRecords:"No matching records found",sEmptyTable:"No data available in table",
sLoadingRecords:"Loading...",sInfo:"Showing _START_ to _END_ of _TOTAL_ entries",sInfoEmpty:"Showing 0 to 0 of 0 entries",sInfoFiltered:"(filtered from _MAX_ total entries)",sInfoPostFix:"",sInfoThousands:",",sSearch:"Search:",sUrl:"",oPaginate:{sFirst:"First",sPrevious:"Previous",sNext:"Next",sLast:"Last"},fnInfoCallback:null};this.aoData=[];this.aiDisplay=[];this.aiDisplayMaster=[];this.aoColumns=[];this.aoHeader=[];this.aoFooter=[];this.iNextId=0;this.asDataSearch=[];this.oPreviousSearch={sSearch:"",
bRegex:false,bSmart:true};this.aoPreSearchCols=[];this.aaSorting=[[0,"asc",0]];this.aaSortingFixed=null;this.asStripeClasses=[];this.asDestroyStripes=[];this.sDestroyWidth=0;this.fnFooterCallback=this.fnHeaderCallback=this.fnRowCallback=null;this.aoDrawCallback=[];this.fnInitComplete=this.fnPreDrawCallback=null;this.sTableId="";this.nTableWrapper=this.nTBody=this.nTFoot=this.nTHead=this.nTable=null;this.bInitialised=this.bDeferLoading=false;this.aoOpenRows=[];this.sDom="lfrtip";this.sPaginationType=
"two_button";this.iCookieDuration=7200;this.sCookiePrefix="SpryMedia_DataTables_";this.fnCookieCallback=null;this.aoStateSave=[];this.aoStateLoad=[];this.sAjaxSource=this.oLoadedState=null;this.sAjaxDataProp="aaData";this.bAjaxDataGet=true;this.jqXHR=null;this.fnServerData=function(a,b,c,d){d.jqXHR=i.ajax({url:a,data:b,success:function(f){i(d.oInstance).trigger("xhr",d);c(f)},dataType:"json",cache:false,error:function(f,e){e=="parsererror"&&alert("DataTables warning: JSON data from server could not be parsed. This is caused by a JSON formatting error.")}})};
this.aoServerParams=[];this.fnFormatNumber=function(a){if(a<1E3)return a;else{var b=a+"";a=b.split("");var c="";b=b.length;for(var d=0;d<b;d++){if(d%3===0&&d!==0)c=this.oLanguage.sInfoThousands+c;c=a[b-d-1]+c}}return c};this.aLengthMenu=[10,25,50,100];this.bDrawing=this.iDraw=0;this.iDrawError=-1;this._iDisplayLength=10;this._iDisplayStart=0;this._iDisplayEnd=10;this._iRecordsDisplay=this._iRecordsTotal=0;this.bJUI=false;this.oClasses=n.oStdClasses;this.bSortCellsTop=this.bSorted=this.bFiltered=false;
this.oInit=null;this.aoDestroyCallback=[]}function s(a){return function(){var b=[A(this[n.iApiIndex])].concat(Array.prototype.slice.call(arguments));return n.oApi[a].apply(this,b)}}function t(a){var b,c,d=a.iInitDisplayStart;if(a.bInitialised===false)setTimeout(function(){t(a)},200);else{Aa(a);X(a);M(a,a.aoHeader);a.nTFoot&&M(a,a.aoFooter);K(a,true);a.oFeatures.bAutoWidth&&ga(a);b=0;for(c=a.aoColumns.length;b<c;b++)if(a.aoColumns[b].sWidth!==null)a.aoColumns[b].nTh.style.width=q(a.aoColumns[b].sWidth);
if(a.oFeatures.bSort)R(a);else if(a.oFeatures.bFilter)N(a,a.oPreviousSearch);else{a.aiDisplay=a.aiDisplayMaster.slice();E(a);C(a)}if(a.sAjaxSource!==null&&!a.oFeatures.bServerSide){c=[];ha(a,c);a.fnServerData.call(a.oInstance,a.sAjaxSource,c,function(f){var e=f;if(a.sAjaxDataProp!=="")e=aa(a.sAjaxDataProp)(f);for(b=0;b<e.length;b++)v(a,e[b]);a.iInitDisplayStart=d;if(a.oFeatures.bSort)R(a);else{a.aiDisplay=a.aiDisplayMaster.slice();E(a);C(a)}K(a,false);w(a,f)},a)}else if(!a.oFeatures.bServerSide){K(a,
false);w(a)}}}function w(a,b){a._bInitComplete=true;if(typeof a.fnInitComplete=="function")typeof b!="undefined"?a.fnInitComplete.call(a.oInstance,a,b):a.fnInitComplete.call(a.oInstance,a)}function y(a,b,c){a.oLanguage=i.extend(true,a.oLanguage,b);typeof b.sEmptyTable=="undefined"&&typeof b.sZeroRecords!="undefined"&&o(a.oLanguage,b,"sZeroRecords","sEmptyTable");typeof b.sLoadingRecords=="undefined"&&typeof b.sZeroRecords!="undefined"&&o(a.oLanguage,b,"sZeroRecords","sLoadingRecords");c&&t(a)}function F(a,
b){var c=a.aoColumns.length;b={sType:null,_bAutoType:true,bVisible:true,bSearchable:true,bSortable:true,asSorting:["asc","desc"],sSortingClass:a.oClasses.sSortable,sSortingClassJUI:a.oClasses.sSortJUI,sTitle:b?b.innerHTML:"",sName:"",sWidth:null,sWidthOrig:null,sClass:null,fnRender:null,bUseRendered:true,iDataSort:c,mDataProp:c,fnGetData:null,fnSetData:null,sSortDataType:"std",sDefaultContent:null,sContentPadding:"",nTh:b?b:p.createElement("th"),nTf:null};a.aoColumns.push(b);if(typeof a.aoPreSearchCols[c]==
"undefined"||a.aoPreSearchCols[c]===null)a.aoPreSearchCols[c]={sSearch:"",bRegex:false,bSmart:true};else{if(typeof a.aoPreSearchCols[c].bRegex=="undefined")a.aoPreSearchCols[c].bRegex=true;if(typeof a.aoPreSearchCols[c].bSmart=="undefined")a.aoPreSearchCols[c].bSmart=true}x(a,c,null)}function x(a,b,c){b=a.aoColumns[b];if(typeof c!="undefined"&&c!==null){if(typeof c.sType!="undefined"){b.sType=c.sType;b._bAutoType=false}o(b,c,"bVisible");o(b,c,"bSearchable");o(b,c,"bSortable");o(b,c,"sTitle");o(b,
c,"sName");o(b,c,"sWidth");o(b,c,"sWidth","sWidthOrig");o(b,c,"sClass");o(b,c,"fnRender");o(b,c,"bUseRendered");o(b,c,"iDataSort");o(b,c,"mDataProp");o(b,c,"asSorting");o(b,c,"sSortDataType");o(b,c,"sDefaultContent");o(b,c,"sContentPadding")}b.fnGetData=aa(b.mDataProp);b.fnSetData=Ba(b.mDataProp);if(!a.oFeatures.bSort)b.bSortable=false;if(!b.bSortable||i.inArray("asc",b.asSorting)==-1&&i.inArray("desc",b.asSorting)==-1){b.sSortingClass=a.oClasses.sSortableNone;b.sSortingClassJUI=""}else if(b.bSortable||
i.inArray("asc",b.asSorting)==-1&&i.inArray("desc",b.asSorting)==-1){b.sSortingClass=a.oClasses.sSortable;b.sSortingClassJUI=a.oClasses.sSortJUI}else if(i.inArray("asc",b.asSorting)!=-1&&i.inArray("desc",b.asSorting)==-1){b.sSortingClass=a.oClasses.sSortableAsc;b.sSortingClassJUI=a.oClasses.sSortJUIAscAllowed}else if(i.inArray("asc",b.asSorting)==-1&&i.inArray("desc",b.asSorting)!=-1){b.sSortingClass=a.oClasses.sSortableDesc;b.sSortingClassJUI=a.oClasses.sSortJUIDescAllowed}}function v(a,b){var c;
c=i.isArray(b)?b.slice():i.extend(true,{},b);b=a.aoData.length;var d={nTr:null,_iId:a.iNextId++,_aData:c,_anHidden:[],_sRowStripe:""};a.aoData.push(d);for(var f,e=0,h=a.aoColumns.length;e<h;e++){c=a.aoColumns[e];typeof c.fnRender=="function"&&c.bUseRendered&&c.mDataProp!==null&&O(a,b,e,c.fnRender({iDataRow:b,iDataColumn:e,aData:d._aData,oSettings:a}));if(c._bAutoType&&c.sType!="string"){f=G(a,b,e,"type");if(f!==null&&f!==""){f=ia(f);if(c.sType===null)c.sType=f;else if(c.sType!=f&&c.sType!="html")c.sType=
"string"}}}a.aiDisplayMaster.push(b);a.oFeatures.bDeferRender||z(a,b);return b}function z(a,b){var c=a.aoData[b],d;if(c.nTr===null){c.nTr=p.createElement("tr");typeof c._aData.DT_RowId!="undefined"&&c.nTr.setAttribute("id",c._aData.DT_RowId);typeof c._aData.DT_RowClass!="undefined"&&i(c.nTr).addClass(c._aData.DT_RowClass);for(var f=0,e=a.aoColumns.length;f<e;f++){var h=a.aoColumns[f];d=p.createElement("td");d.innerHTML=typeof h.fnRender=="function"&&(!h.bUseRendered||h.mDataProp===null)?h.fnRender({iDataRow:b,
iDataColumn:f,aData:c._aData,oSettings:a}):G(a,b,f,"display");if(h.sClass!==null)d.className=h.sClass;if(h.bVisible){c.nTr.appendChild(d);c._anHidden[f]=null}else c._anHidden[f]=d}}}function $(a){var b,c,d,f,e,h,j,k,m;if(a.bDeferLoading||a.sAjaxSource===null){j=a.nTBody.childNodes;b=0;for(c=j.length;b<c;b++)if(j[b].nodeName.toUpperCase()=="TR"){k=a.aoData.length;a.aoData.push({nTr:j[b],_iId:a.iNextId++,_aData:[],_anHidden:[],_sRowStripe:""});a.aiDisplayMaster.push(k);h=j[b].childNodes;d=e=0;for(f=
h.length;d<f;d++){m=h[d].nodeName.toUpperCase();if(m=="TD"||m=="TH"){O(a,k,e,i.trim(h[d].innerHTML));e++}}}}j=ba(a);h=[];b=0;for(c=j.length;b<c;b++){d=0;for(f=j[b].childNodes.length;d<f;d++){e=j[b].childNodes[d];m=e.nodeName.toUpperCase();if(m=="TD"||m=="TH")h.push(e)}}h.length!=j.length*a.aoColumns.length&&J(a,1,"Unexpected number of TD elements. Expected "+j.length*a.aoColumns.length+" and got "+h.length+". DataTables does not support rowspan / colspan in the table body, and there must be one cell for each row/column combination.");
d=0;for(f=a.aoColumns.length;d<f;d++){if(a.aoColumns[d].sTitle===null)a.aoColumns[d].sTitle=a.aoColumns[d].nTh.innerHTML;j=a.aoColumns[d]._bAutoType;m=typeof a.aoColumns[d].fnRender=="function";e=a.aoColumns[d].sClass!==null;k=a.aoColumns[d].bVisible;var u,r;if(j||m||e||!k){b=0;for(c=a.aoData.length;b<c;b++){u=h[b*f+d];if(j&&a.aoColumns[d].sType!="string"){r=G(a,b,d,"type");if(r!==""){r=ia(r);if(a.aoColumns[d].sType===null)a.aoColumns[d].sType=r;else if(a.aoColumns[d].sType!=r&&a.aoColumns[d].sType!=
"html")a.aoColumns[d].sType="string"}}if(m){r=a.aoColumns[d].fnRender({iDataRow:b,iDataColumn:d,aData:a.aoData[b]._aData,oSettings:a});u.innerHTML=r;a.aoColumns[d].bUseRendered&&O(a,b,d,r)}if(e)u.className+=" "+a.aoColumns[d].sClass;if(k)a.aoData[b]._anHidden[d]=null;else{a.aoData[b]._anHidden[d]=u;u.parentNode.removeChild(u)}}}}}function X(a){var b,c,d;a.nTHead.getElementsByTagName("tr");if(a.nTHead.getElementsByTagName("th").length!==0){b=0;for(d=a.aoColumns.length;b<d;b++){c=a.aoColumns[b].nTh;
a.aoColumns[b].sClass!==null&&i(c).addClass(a.aoColumns[b].sClass);if(a.aoColumns[b].sTitle!=c.innerHTML)c.innerHTML=a.aoColumns[b].sTitle}}else{var f=p.createElement("tr");b=0;for(d=a.aoColumns.length;b<d;b++){c=a.aoColumns[b].nTh;c.innerHTML=a.aoColumns[b].sTitle;a.aoColumns[b].sClass!==null&&i(c).addClass(a.aoColumns[b].sClass);f.appendChild(c)}i(a.nTHead).html("")[0].appendChild(f);Y(a.aoHeader,a.nTHead)}if(a.bJUI){b=0;for(d=a.aoColumns.length;b<d;b++){c=a.aoColumns[b].nTh;f=p.createElement("div");
f.className=a.oClasses.sSortJUIWrapper;i(c).contents().appendTo(f);var e=p.createElement("span");e.className=a.oClasses.sSortIcon;f.appendChild(e);c.appendChild(f)}}d=function(){this.onselectstart=function(){return false};return false};if(a.oFeatures.bSort)for(b=0;b<a.aoColumns.length;b++)if(a.aoColumns[b].bSortable!==false){ja(a,a.aoColumns[b].nTh,b);i(a.aoColumns[b].nTh).bind("mousedown.DT",d)}else i(a.aoColumns[b].nTh).addClass(a.oClasses.sSortableNone);a.oClasses.sFooterTH!==""&&i(a.nTFoot).children("tr").children("th").addClass(a.oClasses.sFooterTH);
if(a.nTFoot!==null){c=S(a,null,a.aoFooter);b=0;for(d=a.aoColumns.length;b<d;b++)if(typeof c[b]!="undefined")a.aoColumns[b].nTf=c[b]}}function M(a,b,c){var d,f,e,h=[],j=[],k=a.aoColumns.length;if(typeof c=="undefined")c=false;d=0;for(f=b.length;d<f;d++){h[d]=b[d].slice();h[d].nTr=b[d].nTr;for(e=k-1;e>=0;e--)!a.aoColumns[e].bVisible&&!c&&h[d].splice(e,1);j.push([])}d=0;for(f=h.length;d<f;d++){if(h[d].nTr){a=0;for(e=h[d].nTr.childNodes.length;a<e;a++)h[d].nTr.removeChild(h[d].nTr.childNodes[0])}e=0;
for(b=h[d].length;e<b;e++){k=c=1;if(typeof j[d][e]=="undefined"){h[d].nTr.appendChild(h[d][e].cell);for(j[d][e]=1;typeof h[d+c]!="undefined"&&h[d][e].cell==h[d+c][e].cell;){j[d+c][e]=1;c++}for(;typeof h[d][e+k]!="undefined"&&h[d][e].cell==h[d][e+k].cell;){for(a=0;a<c;a++)j[d+a][e+k]=1;k++}h[d][e].cell.rowSpan=c;h[d][e].cell.colSpan=k}}}}function C(a){var b,c,d=[],f=0,e=false;b=a.asStripeClasses.length;c=a.aoOpenRows.length;if(!(a.fnPreDrawCallback!==null&&a.fnPreDrawCallback.call(a.oInstance,a)===
false)){a.bDrawing=true;if(typeof a.iInitDisplayStart!="undefined"&&a.iInitDisplayStart!=-1){a._iDisplayStart=a.oFeatures.bServerSide?a.iInitDisplayStart:a.iInitDisplayStart>=a.fnRecordsDisplay()?0:a.iInitDisplayStart;a.iInitDisplayStart=-1;E(a)}if(a.bDeferLoading){a.bDeferLoading=false;a.iDraw++}else if(a.oFeatures.bServerSide){if(!a.bDestroying&&!Ca(a))return}else a.iDraw++;if(a.aiDisplay.length!==0){var h=a._iDisplayStart,j=a._iDisplayEnd;if(a.oFeatures.bServerSide){h=0;j=a.aoData.length}for(h=
h;h<j;h++){var k=a.aoData[a.aiDisplay[h]];k.nTr===null&&z(a,a.aiDisplay[h]);var m=k.nTr;if(b!==0){var u=a.asStripeClasses[f%b];if(k._sRowStripe!=u){i(m).removeClass(k._sRowStripe).addClass(u);k._sRowStripe=u}}if(typeof a.fnRowCallback=="function"){m=a.fnRowCallback.call(a.oInstance,m,a.aoData[a.aiDisplay[h]]._aData,f,h);if(!m&&!e){J(a,0,"A node was not returned by fnRowCallback");e=true}}d.push(m);f++;if(c!==0)for(k=0;k<c;k++)m==a.aoOpenRows[k].nParent&&d.push(a.aoOpenRows[k].nTr)}}else{d[0]=p.createElement("tr");
if(typeof a.asStripeClasses[0]!="undefined")d[0].className=a.asStripeClasses[0];e=a.oLanguage.sZeroRecords.replace("_MAX_",a.fnFormatNumber(a.fnRecordsTotal()));if(a.iDraw==1&&a.sAjaxSource!==null&&!a.oFeatures.bServerSide)e=a.oLanguage.sLoadingRecords;else if(typeof a.oLanguage.sEmptyTable!="undefined"&&a.fnRecordsTotal()===0)e=a.oLanguage.sEmptyTable;b=p.createElement("td");b.setAttribute("valign","top");b.colSpan=Z(a);b.className=a.oClasses.sRowEmpty;b.innerHTML=e;d[f].appendChild(b)}typeof a.fnHeaderCallback==
"function"&&a.fnHeaderCallback.call(a.oInstance,i(a.nTHead).children("tr")[0],ca(a),a._iDisplayStart,a.fnDisplayEnd(),a.aiDisplay);typeof a.fnFooterCallback=="function"&&a.fnFooterCallback.call(a.oInstance,i(a.nTFoot).children("tr")[0],ca(a),a._iDisplayStart,a.fnDisplayEnd(),a.aiDisplay);f=p.createDocumentFragment();b=p.createDocumentFragment();if(a.nTBody){e=a.nTBody.parentNode;b.appendChild(a.nTBody);if(!a.oScroll.bInfinite||!a._bInitComplete||a.bSorted||a.bFiltered){c=a.nTBody.childNodes;for(b=
c.length-1;b>=0;b--)c[b].parentNode.removeChild(c[b])}b=0;for(c=d.length;b<c;b++)f.appendChild(d[b]);a.nTBody.appendChild(f);e!==null&&e.appendChild(a.nTBody)}for(b=a.aoDrawCallback.length-1;b>=0;b--)a.aoDrawCallback[b].fn.call(a.oInstance,a);i(a.oInstance).trigger("draw",a);a.bSorted=false;a.bFiltered=false;a.bDrawing=false;if(a.oFeatures.bServerSide){K(a,false);typeof a._bInitComplete=="undefined"&&w(a)}}}function da(a){if(a.oFeatures.bSort)R(a,a.oPreviousSearch);else if(a.oFeatures.bFilter)N(a,
a.oPreviousSearch);else{E(a);C(a)}}function Ca(a){if(a.bAjaxDataGet){a.iDraw++;K(a,true);var b=Da(a);ha(a,b);a.fnServerData.call(a.oInstance,a.sAjaxSource,b,function(c){Ea(a,c)},a);return false}else return true}function Da(a){var b=a.aoColumns.length,c=[],d,f;c.push({name:"sEcho",value:a.iDraw});c.push({name:"iColumns",value:b});c.push({name:"sColumns",value:ka(a)});c.push({name:"iDisplayStart",value:a._iDisplayStart});c.push({name:"iDisplayLength",value:a.oFeatures.bPaginate!==false?a._iDisplayLength:
-1});for(f=0;f<b;f++){d=a.aoColumns[f].mDataProp;c.push({name:"mDataProp_"+f,value:typeof d=="function"?"function":d})}if(a.oFeatures.bFilter!==false){c.push({name:"sSearch",value:a.oPreviousSearch.sSearch});c.push({name:"bRegex",value:a.oPreviousSearch.bRegex});for(f=0;f<b;f++){c.push({name:"sSearch_"+f,value:a.aoPreSearchCols[f].sSearch});c.push({name:"bRegex_"+f,value:a.aoPreSearchCols[f].bRegex});c.push({name:"bSearchable_"+f,value:a.aoColumns[f].bSearchable})}}if(a.oFeatures.bSort!==false){d=
a.aaSortingFixed!==null?a.aaSortingFixed.length:0;var e=a.aaSorting.length;c.push({name:"iSortingCols",value:d+e});for(f=0;f<d;f++){c.push({name:"iSortCol_"+f,value:a.aaSortingFixed[f][0]});c.push({name:"sSortDir_"+f,value:a.aaSortingFixed[f][1]})}for(f=0;f<e;f++){c.push({name:"iSortCol_"+(f+d),value:a.aaSorting[f][0]});c.push({name:"sSortDir_"+(f+d),value:a.aaSorting[f][1]})}for(f=0;f<b;f++)c.push({name:"bSortable_"+f,value:a.aoColumns[f].bSortable})}return c}function ha(a,b){for(var c=0,d=a.aoServerParams.length;c<
d;c++)a.aoServerParams[c].fn.call(a.oInstance,b)}function Ea(a,b){if(typeof b.sEcho!="undefined")if(b.sEcho*1<a.iDraw)return;else a.iDraw=b.sEcho*1;if(!a.oScroll.bInfinite||a.oScroll.bInfinite&&(a.bSorted||a.bFiltered))la(a);a._iRecordsTotal=b.iTotalRecords;a._iRecordsDisplay=b.iTotalDisplayRecords;var c=ka(a);if(c=typeof b.sColumns!="undefined"&&c!==""&&b.sColumns!=c)var d=Fa(a,b.sColumns);b=aa(a.sAjaxDataProp)(b);for(var f=0,e=b.length;f<e;f++)if(c){for(var h=[],j=0,k=a.aoColumns.length;j<k;j++)h.push(b[f][d[j]]);
v(a,h)}else v(a,b[f]);a.aiDisplay=a.aiDisplayMaster.slice();a.bAjaxDataGet=false;C(a);a.bAjaxDataGet=true;K(a,false)}function Aa(a){var b=p.createElement("div");a.nTable.parentNode.insertBefore(b,a.nTable);a.nTableWrapper=p.createElement("div");a.nTableWrapper.className=a.oClasses.sWrapper;a.sTableId!==""&&a.nTableWrapper.setAttribute("id",a.sTableId+"_wrapper");a.nTableReinsertBefore=a.nTable.nextSibling;for(var c=a.nTableWrapper,d=a.sDom.split(""),f,e,h,j,k,m,u,r=0;r<d.length;r++){e=0;h=d[r];if(h==
"<"){j=p.createElement("div");k=d[r+1];if(k=="'"||k=='"'){m="";for(u=2;d[r+u]!=k;){m+=d[r+u];u++}if(m=="H")m="fg-toolbar ui-toolbar ui-widget-header ui-corner-tl ui-corner-tr ui-helper-clearfix";else if(m=="F")m="fg-toolbar ui-toolbar ui-widget-header ui-corner-bl ui-corner-br ui-helper-clearfix";if(m.indexOf(".")!=-1){k=m.split(".");j.setAttribute("id",k[0].substr(1,k[0].length-1));j.className=k[1]}else if(m.charAt(0)=="#")j.setAttribute("id",m.substr(1,m.length-1));else j.className=m;r+=u}c.appendChild(j);
c=j}else if(h==">")c=c.parentNode;else if(h=="l"&&a.oFeatures.bPaginate&&a.oFeatures.bLengthChange){f=Ga(a);e=1}else if(h=="f"&&a.oFeatures.bFilter){f=Ha(a);e=1}else if(h=="r"&&a.oFeatures.bProcessing){f=Ia(a);e=1}else if(h=="t"){f=Ja(a);e=1}else if(h=="i"&&a.oFeatures.bInfo){f=Ka(a);e=1}else if(h=="p"&&a.oFeatures.bPaginate){f=La(a);e=1}else if(n.aoFeatures.length!==0){j=n.aoFeatures;u=0;for(k=j.length;u<k;u++)if(h==j[u].cFeature){if(f=j[u].fnInit(a))e=1;break}}if(e==1&&f!==null){if(typeof a.aanFeatures[h]!=
"object")a.aanFeatures[h]=[];a.aanFeatures[h].push(f);c.appendChild(f)}}b.parentNode.replaceChild(a.nTableWrapper,b)}function Ja(a){if(a.oScroll.sX===""&&a.oScroll.sY==="")return a.nTable;var b=p.createElement("div"),c=p.createElement("div"),d=p.createElement("div"),f=p.createElement("div"),e=p.createElement("div"),h=p.createElement("div"),j=a.nTable.cloneNode(false),k=a.nTable.cloneNode(false),m=a.nTable.getElementsByTagName("thead")[0],u=a.nTable.getElementsByTagName("tfoot").length===0?null:a.nTable.getElementsByTagName("tfoot")[0],
r=typeof g.bJQueryUI!="undefined"&&g.bJQueryUI?n.oJUIClasses:n.oStdClasses;c.appendChild(d);e.appendChild(h);f.appendChild(a.nTable);b.appendChild(c);b.appendChild(f);d.appendChild(j);j.appendChild(m);if(u!==null){b.appendChild(e);h.appendChild(k);k.appendChild(u)}b.className=r.sScrollWrapper;c.className=r.sScrollHead;d.className=r.sScrollHeadInner;f.className=r.sScrollBody;e.className=r.sScrollFoot;h.className=r.sScrollFootInner;if(a.oScroll.bAutoCss){c.style.overflow="hidden";c.style.position="relative";
e.style.overflow="hidden";f.style.overflow="auto"}c.style.border="0";c.style.width="100%";e.style.border="0";d.style.width="150%";j.removeAttribute("id");j.style.marginLeft="0";a.nTable.style.marginLeft="0";if(u!==null){k.removeAttribute("id");k.style.marginLeft="0"}d=i(a.nTable).children("caption");h=0;for(k=d.length;h<k;h++)j.appendChild(d[h]);if(a.oScroll.sX!==""){c.style.width=q(a.oScroll.sX);f.style.width=q(a.oScroll.sX);if(u!==null)e.style.width=q(a.oScroll.sX);i(f).scroll(function(){c.scrollLeft=
this.scrollLeft;if(u!==null)e.scrollLeft=this.scrollLeft})}if(a.oScroll.sY!=="")f.style.height=q(a.oScroll.sY);a.aoDrawCallback.push({fn:Ma,sName:"scrolling"});a.oScroll.bInfinite&&i(f).scroll(function(){if(!a.bDrawing)if(i(this).scrollTop()+i(this).height()>i(a.nTable).height()-a.oScroll.iLoadGap)if(a.fnDisplayEnd()<a.fnRecordsDisplay()){ma(a,"next");E(a);C(a)}});a.nScrollHead=c;a.nScrollFoot=e;return b}function Ma(a){var b=a.nScrollHead.getElementsByTagName("div")[0],c=b.getElementsByTagName("table")[0],
d=a.nTable.parentNode,f,e,h,j,k,m,u,r,H=[],L=a.nTFoot!==null?a.nScrollFoot.getElementsByTagName("div")[0]:null,T=a.nTFoot!==null?L.getElementsByTagName("table")[0]:null,B=i.browser.msie&&i.browser.version<=7;h=a.nTable.getElementsByTagName("thead");h.length>0&&a.nTable.removeChild(h[0]);if(a.nTFoot!==null){k=a.nTable.getElementsByTagName("tfoot");k.length>0&&a.nTable.removeChild(k[0])}h=a.nTHead.cloneNode(true);a.nTable.insertBefore(h,a.nTable.childNodes[0]);if(a.nTFoot!==null){k=a.nTFoot.cloneNode(true);
a.nTable.insertBefore(k,a.nTable.childNodes[1])}if(a.oScroll.sX===""){d.style.width="100%";b.parentNode.style.width="100%"}var U=S(a,h);f=0;for(e=U.length;f<e;f++){u=Na(a,f);U[f].style.width=a.aoColumns[u].sWidth}a.nTFoot!==null&&P(function(I){I.style.width=""},k.getElementsByTagName("tr"));f=i(a.nTable).outerWidth();if(a.oScroll.sX===""){a.nTable.style.width="100%";if(B&&(d.scrollHeight>d.offsetHeight||i(d).css("overflow-y")=="scroll"))a.nTable.style.width=q(i(a.nTable).outerWidth()-a.oScroll.iBarWidth)}else if(a.oScroll.sXInner!==
"")a.nTable.style.width=q(a.oScroll.sXInner);else if(f==i(d).width()&&i(d).height()<i(a.nTable).height()){a.nTable.style.width=q(f-a.oScroll.iBarWidth);if(i(a.nTable).outerWidth()>f-a.oScroll.iBarWidth)a.nTable.style.width=q(f)}else a.nTable.style.width=q(f);f=i(a.nTable).outerWidth();e=a.nTHead.getElementsByTagName("tr");h=h.getElementsByTagName("tr");P(function(I,na){m=I.style;m.paddingTop="0";m.paddingBottom="0";m.borderTopWidth="0";m.borderBottomWidth="0";m.height=0;r=i(I).width();na.style.width=
q(r);H.push(r)},h,e);i(h).height(0);if(a.nTFoot!==null){j=k.getElementsByTagName("tr");k=a.nTFoot.getElementsByTagName("tr");P(function(I,na){m=I.style;m.paddingTop="0";m.paddingBottom="0";m.borderTopWidth="0";m.borderBottomWidth="0";m.height=0;r=i(I).width();na.style.width=q(r);H.push(r)},j,k);i(j).height(0)}P(function(I){I.innerHTML="";I.style.width=q(H.shift())},h);a.nTFoot!==null&&P(function(I){I.innerHTML="";I.style.width=q(H.shift())},j);if(i(a.nTable).outerWidth()<f){j=d.scrollHeight>d.offsetHeight||
i(d).css("overflow-y")=="scroll"?f+a.oScroll.iBarWidth:f;if(B&&(d.scrollHeight>d.offsetHeight||i(d).css("overflow-y")=="scroll"))a.nTable.style.width=q(j-a.oScroll.iBarWidth);d.style.width=q(j);b.parentNode.style.width=q(j);if(a.nTFoot!==null)L.parentNode.style.width=q(j);if(a.oScroll.sX==="")J(a,1,"The table cannot fit into the current element which will cause column misalignment. The table has been drawn at its minimum possible width.");else a.oScroll.sXInner!==""&&J(a,1,"The table cannot fit into the current element which will cause column misalignment. Increase the sScrollXInner value or remove it to allow automatic calculation")}else{d.style.width=
q("100%");b.parentNode.style.width=q("100%");if(a.nTFoot!==null)L.parentNode.style.width=q("100%")}if(a.oScroll.sY==="")if(B)d.style.height=q(a.nTable.offsetHeight+a.oScroll.iBarWidth);if(a.oScroll.sY!==""&&a.oScroll.bCollapse){d.style.height=q(a.oScroll.sY);B=a.oScroll.sX!==""&&a.nTable.offsetWidth>d.offsetWidth?a.oScroll.iBarWidth:0;if(a.nTable.offsetHeight<d.offsetHeight)d.style.height=q(i(a.nTable).height()+B)}B=i(a.nTable).outerWidth();c.style.width=q(B);b.style.width=q(B+a.oScroll.iBarWidth);
if(a.nTFoot!==null){L.style.width=q(a.nTable.offsetWidth+a.oScroll.iBarWidth);T.style.width=q(a.nTable.offsetWidth)}if(a.bSorted||a.bFiltered)d.scrollTop=0}function ea(a){if(a.oFeatures.bAutoWidth===false)return false;ga(a);for(var b=0,c=a.aoColumns.length;b<c;b++)a.aoColumns[b].nTh.style.width=a.aoColumns[b].sWidth}function Ha(a){var b=a.oLanguage.sSearch;b=b.indexOf("_INPUT_")!==-1?b.replace("_INPUT_",'<input type="text" />'):b===""?'<input type="text" />':b+' <input type="text" />';var c=p.createElement("div");
c.className=a.oClasses.sFilter;c.innerHTML="<label>"+b+"</label>";a.sTableId!==""&&typeof a.aanFeatures.f=="undefined"&&c.setAttribute("id",a.sTableId+"_filter");b=i("input",c);b.val(a.oPreviousSearch.sSearch.replace('"',"&quot;"));b.bind("keyup.DT",function(){for(var d=a.aanFeatures.f,f=0,e=d.length;f<e;f++)d[f]!=i(this).parents("div.dataTables_filter")[0]&&i("input",d[f]).val(this.value);this.value!=a.oPreviousSearch.sSearch&&N(a,{sSearch:this.value,bRegex:a.oPreviousSearch.bRegex,bSmart:a.oPreviousSearch.bSmart})});
b.bind("keypress.DT",function(d){if(d.keyCode==13)return false});return c}function N(a,b,c){Oa(a,b.sSearch,c,b.bRegex,b.bSmart);for(b=0;b<a.aoPreSearchCols.length;b++)Pa(a,a.aoPreSearchCols[b].sSearch,b,a.aoPreSearchCols[b].bRegex,a.aoPreSearchCols[b].bSmart);n.afnFiltering.length!==0&&Qa(a);a.bFiltered=true;i(a.oInstance).trigger("filter",a);a._iDisplayStart=0;E(a);C(a);oa(a,0)}function Qa(a){for(var b=n.afnFiltering,c=0,d=b.length;c<d;c++)for(var f=0,e=0,h=a.aiDisplay.length;e<h;e++){var j=a.aiDisplay[e-
f];if(!b[c](a,fa(a,j,"filter"),j)){a.aiDisplay.splice(e-f,1);f++}}}function Pa(a,b,c,d,f){if(b!==""){var e=0;b=pa(b,d,f);for(d=a.aiDisplay.length-1;d>=0;d--){f=qa(G(a,a.aiDisplay[d],c,"filter"),a.aoColumns[c].sType);if(!b.test(f)){a.aiDisplay.splice(d,1);e++}}}}function Oa(a,b,c,d,f){var e=pa(b,d,f);if(typeof c=="undefined"||c===null)c=0;if(n.afnFiltering.length!==0)c=1;if(b.length<=0){a.aiDisplay.splice(0,a.aiDisplay.length);a.aiDisplay=a.aiDisplayMaster.slice()}else if(a.aiDisplay.length==a.aiDisplayMaster.length||
a.oPreviousSearch.sSearch.length>b.length||c==1||b.indexOf(a.oPreviousSearch.sSearch)!==0){a.aiDisplay.splice(0,a.aiDisplay.length);oa(a,1);for(c=0;c<a.aiDisplayMaster.length;c++)e.test(a.asDataSearch[c])&&a.aiDisplay.push(a.aiDisplayMaster[c])}else{var h=0;for(c=0;c<a.asDataSearch.length;c++)if(!e.test(a.asDataSearch[c])){a.aiDisplay.splice(c-h,1);h++}}a.oPreviousSearch.sSearch=b;a.oPreviousSearch.bRegex=d;a.oPreviousSearch.bSmart=f}function oa(a,b){if(!a.oFeatures.bServerSide){a.asDataSearch.splice(0,
a.asDataSearch.length);b=typeof b!="undefined"&&b==1?a.aiDisplayMaster:a.aiDisplay;for(var c=0,d=b.length;c<d;c++)a.asDataSearch[c]=ra(a,fa(a,b[c],"filter"))}}function ra(a,b){var c="";if(typeof a.__nTmpFilter=="undefined")a.__nTmpFilter=p.createElement("div");for(var d=a.__nTmpFilter,f=0,e=a.aoColumns.length;f<e;f++)if(a.aoColumns[f].bSearchable)c+=qa(b[f],a.aoColumns[f].sType)+"  ";if(c.indexOf("&")!==-1){d.innerHTML=c;c=d.textContent?d.textContent:d.innerText;c=c.replace(/\n/g," ").replace(/\r/g,
"")}return c}function pa(a,b,c){if(c){a=b?a.split(" "):sa(a).split(" ");a="^(?=.*?"+a.join(")(?=.*?")+").*$";return new RegExp(a,"i")}else{a=b?a:sa(a);return new RegExp(a,"i")}}function qa(a,b){if(typeof n.ofnSearch[b]=="function")return n.ofnSearch[b](a);else if(b=="html")return a.replace(/\n/g," ").replace(/<.*?>/g,"");else if(typeof a=="string")return a.replace(/\n/g," ");else if(a===null)return"";return a}function R(a,b){var c,d,f,e,h=[],j=[],k=n.oSort;d=a.aoData;var m=a.aoColumns;if(!a.oFeatures.bServerSide&&
(a.aaSorting.length!==0||a.aaSortingFixed!==null)){h=a.aaSortingFixed!==null?a.aaSortingFixed.concat(a.aaSorting):a.aaSorting.slice();for(c=0;c<h.length;c++){var u=h[c][0];f=ta(a,u);e=a.aoColumns[u].sSortDataType;if(typeof n.afnSortData[e]!="undefined"){var r=n.afnSortData[e](a,u,f);f=0;for(e=d.length;f<e;f++)O(a,f,u,r[f])}}c=0;for(d=a.aiDisplayMaster.length;c<d;c++)j[a.aiDisplayMaster[c]]=c;var H=h.length;a.aiDisplayMaster.sort(function(L,T){var B,U;for(c=0;c<H;c++){B=m[h[c][0]].iDataSort;U=m[B].sType;
B=k[(U?U:"string")+"-"+h[c][1]](G(a,L,B,"sort"),G(a,T,B,"sort"));if(B!==0)return B}return k["numeric-asc"](j[L],j[T])})}if((typeof b=="undefined"||b)&&!a.oFeatures.bDeferRender)V(a);a.bSorted=true;i(a.oInstance).trigger("sort",a);if(a.oFeatures.bFilter)N(a,a.oPreviousSearch,1);else{a.aiDisplay=a.aiDisplayMaster.slice();a._iDisplayStart=0;E(a);C(a)}}function ja(a,b,c,d){i(b).bind("click.DT",function(f){if(a.aoColumns[c].bSortable!==false){var e=function(){var h,j;if(f.shiftKey){for(var k=false,m=0;m<
a.aaSorting.length;m++)if(a.aaSorting[m][0]==c){k=true;h=a.aaSorting[m][0];j=a.aaSorting[m][2]+1;if(typeof a.aoColumns[h].asSorting[j]=="undefined")a.aaSorting.splice(m,1);else{a.aaSorting[m][1]=a.aoColumns[h].asSorting[j];a.aaSorting[m][2]=j}break}k===false&&a.aaSorting.push([c,a.aoColumns[c].asSorting[0],0])}else if(a.aaSorting.length==1&&a.aaSorting[0][0]==c){h=a.aaSorting[0][0];j=a.aaSorting[0][2]+1;if(typeof a.aoColumns[h].asSorting[j]=="undefined")j=0;a.aaSorting[0][1]=a.aoColumns[h].asSorting[j];
a.aaSorting[0][2]=j}else{a.aaSorting.splice(0,a.aaSorting.length);a.aaSorting.push([c,a.aoColumns[c].asSorting[0],0])}R(a)};if(a.oFeatures.bProcessing){K(a,true);setTimeout(function(){e();a.oFeatures.bServerSide||K(a,false)},0)}else e();typeof d=="function"&&d(a)}})}function V(a){var b,c,d,f,e,h=a.aoColumns.length,j=a.oClasses;for(b=0;b<h;b++)a.aoColumns[b].bSortable&&i(a.aoColumns[b].nTh).removeClass(j.sSortAsc+" "+j.sSortDesc+" "+a.aoColumns[b].sSortingClass);f=a.aaSortingFixed!==null?a.aaSortingFixed.concat(a.aaSorting):
a.aaSorting.slice();for(b=0;b<a.aoColumns.length;b++)if(a.aoColumns[b].bSortable){e=a.aoColumns[b].sSortingClass;d=-1;for(c=0;c<f.length;c++)if(f[c][0]==b){e=f[c][1]=="asc"?j.sSortAsc:j.sSortDesc;d=c;break}i(a.aoColumns[b].nTh).addClass(e);if(a.bJUI){c=i("span",a.aoColumns[b].nTh);c.removeClass(j.sSortJUIAsc+" "+j.sSortJUIDesc+" "+j.sSortJUI+" "+j.sSortJUIAscAllowed+" "+j.sSortJUIDescAllowed);c.addClass(d==-1?a.aoColumns[b].sSortingClassJUI:f[d][1]=="asc"?j.sSortJUIAsc:j.sSortJUIDesc)}}else i(a.aoColumns[b].nTh).addClass(a.aoColumns[b].sSortingClass);
e=j.sSortColumn;if(a.oFeatures.bSort&&a.oFeatures.bSortClasses){d=Q(a);if(a.oFeatures.bDeferRender)i(d).removeClass(e+"1 "+e+"2 "+e+"3");else if(d.length>=h)for(b=0;b<h;b++)if(d[b].className.indexOf(e+"1")!=-1){c=0;for(a=d.length/h;c<a;c++)d[h*c+b].className=i.trim(d[h*c+b].className.replace(e+"1",""))}else if(d[b].className.indexOf(e+"2")!=-1){c=0;for(a=d.length/h;c<a;c++)d[h*c+b].className=i.trim(d[h*c+b].className.replace(e+"2",""))}else if(d[b].className.indexOf(e+"3")!=-1){c=0;for(a=d.length/
h;c<a;c++)d[h*c+b].className=i.trim(d[h*c+b].className.replace(" "+e+"3",""))}j=1;var k;for(b=0;b<f.length;b++){k=parseInt(f[b][0],10);c=0;for(a=d.length/h;c<a;c++)d[h*c+k].className+=" "+e+j;j<3&&j++}}}function La(a){if(a.oScroll.bInfinite)return null;var b=p.createElement("div");b.className=a.oClasses.sPaging+a.sPaginationType;n.oPagination[a.sPaginationType].fnInit(a,b,function(c){E(c);C(c)});typeof a.aanFeatures.p=="undefined"&&a.aoDrawCallback.push({fn:function(c){n.oPagination[c.sPaginationType].fnUpdate(c,
function(d){E(d);C(d)})},sName:"pagination"});return b}function ma(a,b){var c=a._iDisplayStart;if(b=="first")a._iDisplayStart=0;else if(b=="previous"){a._iDisplayStart=a._iDisplayLength>=0?a._iDisplayStart-a._iDisplayLength:0;if(a._iDisplayStart<0)a._iDisplayStart=0}else if(b=="next")if(a._iDisplayLength>=0){if(a._iDisplayStart+a._iDisplayLength<a.fnRecordsDisplay())a._iDisplayStart+=a._iDisplayLength}else a._iDisplayStart=0;else if(b=="last")if(a._iDisplayLength>=0){b=parseInt((a.fnRecordsDisplay()-
1)/a._iDisplayLength,10)+1;a._iDisplayStart=(b-1)*a._iDisplayLength}else a._iDisplayStart=0;else J(a,0,"Unknown paging action: "+b);i(a.oInstance).trigger("page",a);return c!=a._iDisplayStart}function Ka(a){var b=p.createElement("div");b.className=a.oClasses.sInfo;if(typeof a.aanFeatures.i=="undefined"){a.aoDrawCallback.push({fn:Ra,sName:"information"});a.sTableId!==""&&b.setAttribute("id",a.sTableId+"_info")}return b}function Ra(a){if(!(!a.oFeatures.bInfo||a.aanFeatures.i.length===0)){var b=a._iDisplayStart+
1,c=a.fnDisplayEnd(),d=a.fnRecordsTotal(),f=a.fnRecordsDisplay(),e=a.fnFormatNumber(b),h=a.fnFormatNumber(c),j=a.fnFormatNumber(d),k=a.fnFormatNumber(f);if(a.oScroll.bInfinite)e=a.fnFormatNumber(1);e=a.fnRecordsDisplay()===0&&a.fnRecordsDisplay()==a.fnRecordsTotal()?a.oLanguage.sInfoEmpty+a.oLanguage.sInfoPostFix:a.fnRecordsDisplay()===0?a.oLanguage.sInfoEmpty+" "+a.oLanguage.sInfoFiltered.replace("_MAX_",j)+a.oLanguage.sInfoPostFix:a.fnRecordsDisplay()==a.fnRecordsTotal()?a.oLanguage.sInfo.replace("_START_",
e).replace("_END_",h).replace("_TOTAL_",k)+a.oLanguage.sInfoPostFix:a.oLanguage.sInfo.replace("_START_",e).replace("_END_",h).replace("_TOTAL_",k)+" "+a.oLanguage.sInfoFiltered.replace("_MAX_",a.fnFormatNumber(a.fnRecordsTotal()))+a.oLanguage.sInfoPostFix;if(a.oLanguage.fnInfoCallback!==null)e=a.oLanguage.fnInfoCallback(a,b,c,d,f,e);a=a.aanFeatures.i;b=0;for(c=a.length;b<c;b++)i(a[b]).html(e)}}function Ga(a){if(a.oScroll.bInfinite)return null;var b='<select size="1" '+(a.sTableId===""?"":'name="'+
a.sTableId+'_length"')+">",c,d;if(a.aLengthMenu.length==2&&typeof a.aLengthMenu[0]=="object"&&typeof a.aLengthMenu[1]=="object"){c=0;for(d=a.aLengthMenu[0].length;c<d;c++)b+='<option value="'+a.aLengthMenu[0][c]+'">'+a.aLengthMenu[1][c]+"</option>"}else{c=0;for(d=a.aLengthMenu.length;c<d;c++)b+='<option value="'+a.aLengthMenu[c]+'">'+a.aLengthMenu[c]+"</option>"}b+="</select>";var f=p.createElement("div");a.sTableId!==""&&typeof a.aanFeatures.l=="undefined"&&f.setAttribute("id",a.sTableId+"_length");
f.className=a.oClasses.sLength;f.innerHTML="<label>"+a.oLanguage.sLengthMenu.replace("_MENU_",b)+"</label>";i('select option[value="'+a._iDisplayLength+'"]',f).attr("selected",true);i("select",f).bind("change.DT",function(){var e=i(this).val(),h=a.aanFeatures.l;c=0;for(d=h.length;c<d;c++)h[c]!=this.parentNode&&i("select",h[c]).val(e);a._iDisplayLength=parseInt(e,10);E(a);if(a.fnDisplayEnd()==a.fnRecordsDisplay()){a._iDisplayStart=a.fnDisplayEnd()-a._iDisplayLength;if(a._iDisplayStart<0)a._iDisplayStart=
0}if(a._iDisplayLength==-1)a._iDisplayStart=0;C(a)});return f}function Ia(a){var b=p.createElement("div");a.sTableId!==""&&typeof a.aanFeatures.r=="undefined"&&b.setAttribute("id",a.sTableId+"_processing");b.innerHTML=a.oLanguage.sProcessing;b.className=a.oClasses.sProcessing;a.nTable.parentNode.insertBefore(b,a.nTable);return b}function K(a,b){if(a.oFeatures.bProcessing){a=a.aanFeatures.r;for(var c=0,d=a.length;c<d;c++)a[c].style.visibility=b?"visible":"hidden"}}function Na(a,b){for(var c=-1,d=0;d<
a.aoColumns.length;d++){a.aoColumns[d].bVisible===true&&c++;if(c==b)return d}return null}function ta(a,b){for(var c=-1,d=0;d<a.aoColumns.length;d++){a.aoColumns[d].bVisible===true&&c++;if(d==b)return a.aoColumns[d].bVisible===true?c:null}return null}function W(a,b){var c,d;c=a._iDisplayStart;for(d=a._iDisplayEnd;c<d;c++)if(a.aoData[a.aiDisplay[c]].nTr==b)return a.aiDisplay[c];c=0;for(d=a.aoData.length;c<d;c++)if(a.aoData[c].nTr==b)return c;return null}function Z(a){for(var b=0,c=0;c<a.aoColumns.length;c++)a.aoColumns[c].bVisible===
true&&b++;return b}function E(a){a._iDisplayEnd=a.oFeatures.bPaginate===false?a.aiDisplay.length:a._iDisplayStart+a._iDisplayLength>a.aiDisplay.length||a._iDisplayLength==-1?a.aiDisplay.length:a._iDisplayStart+a._iDisplayLength}function Sa(a,b){if(!a||a===null||a==="")return 0;if(typeof b=="undefined")b=p.getElementsByTagName("body")[0];var c=p.createElement("div");c.style.width=q(a);b.appendChild(c);a=c.offsetWidth;b.removeChild(c);return a}function ga(a){var b=0,c,d=0,f=a.aoColumns.length,e,h=i("th",
a.nTHead);for(e=0;e<f;e++)if(a.aoColumns[e].bVisible){d++;if(a.aoColumns[e].sWidth!==null){c=Sa(a.aoColumns[e].sWidthOrig,a.nTable.parentNode);if(c!==null)a.aoColumns[e].sWidth=q(c);b++}}if(f==h.length&&b===0&&d==f&&a.oScroll.sX===""&&a.oScroll.sY==="")for(e=0;e<a.aoColumns.length;e++){c=i(h[e]).width();if(c!==null)a.aoColumns[e].sWidth=q(c)}else{b=a.nTable.cloneNode(false);e=a.nTHead.cloneNode(true);d=p.createElement("tbody");c=p.createElement("tr");b.removeAttribute("id");b.appendChild(e);if(a.nTFoot!==
null){b.appendChild(a.nTFoot.cloneNode(true));P(function(k){k.style.width=""},b.getElementsByTagName("tr"))}b.appendChild(d);d.appendChild(c);d=i("thead th",b);if(d.length===0)d=i("tbody tr:eq(0)>td",b);h=S(a,e);for(e=d=0;e<f;e++){var j=a.aoColumns[e];if(j.bVisible&&j.sWidthOrig!==null&&j.sWidthOrig!=="")h[e-d].style.width=q(j.sWidthOrig);else if(j.bVisible)h[e-d].style.width="";else d++}for(e=0;e<f;e++)if(a.aoColumns[e].bVisible){d=Ta(a,e);if(d!==null){d=d.cloneNode(true);if(a.aoColumns[e].sContentPadding!==
"")d.innerHTML+=a.aoColumns[e].sContentPadding;c.appendChild(d)}}f=a.nTable.parentNode;f.appendChild(b);if(a.oScroll.sX!==""&&a.oScroll.sXInner!=="")b.style.width=q(a.oScroll.sXInner);else if(a.oScroll.sX!==""){b.style.width="";if(i(b).width()<f.offsetWidth)b.style.width=q(f.offsetWidth)}else if(a.oScroll.sY!=="")b.style.width=q(f.offsetWidth);b.style.visibility="hidden";Ua(a,b);f=i("tbody tr:eq(0)",b).children();if(f.length===0)f=S(a,i("thead",b)[0]);if(a.oScroll.sX!==""){for(e=d=c=0;e<a.aoColumns.length;e++)if(a.aoColumns[e].bVisible){c+=
a.aoColumns[e].sWidthOrig===null?i(f[d]).outerWidth():parseInt(a.aoColumns[e].sWidth.replace("px",""),10)+(i(f[d]).outerWidth()-i(f[d]).width());d++}b.style.width=q(c);a.nTable.style.width=q(c)}for(e=d=0;e<a.aoColumns.length;e++)if(a.aoColumns[e].bVisible){c=i(f[d]).width();if(c!==null&&c>0)a.aoColumns[e].sWidth=q(c);d++}a.nTable.style.width=q(i(b).outerWidth());b.parentNode.removeChild(b)}}function Ua(a,b){if(a.oScroll.sX===""&&a.oScroll.sY!==""){i(b).width();b.style.width=q(i(b).outerWidth()-a.oScroll.iBarWidth)}else if(a.oScroll.sX!==
"")b.style.width=q(i(b).outerWidth())}function Ta(a,b){var c=Va(a,b);if(c<0)return null;if(a.aoData[c].nTr===null){var d=p.createElement("td");d.innerHTML=G(a,c,b,"");return d}return Q(a,c)[b]}function Va(a,b){for(var c=-1,d=-1,f=0;f<a.aoData.length;f++){var e=G(a,f,b,"display")+"";e=e.replace(/<.*?>/g,"");if(e.length>c){c=e.length;d=f}}return d}function q(a){if(a===null)return"0px";if(typeof a=="number"){if(a<0)return"0px";return a+"px"}var b=a.charCodeAt(a.length-1);if(b<48||b>57)return a;return a+
"px"}function Za(a,b){if(a.length!=b.length)return 1;for(var c=0;c<a.length;c++)if(a[c]!=b[c])return 2;return 0}function ia(a){for(var b=n.aTypes,c=b.length,d=0;d<c;d++){var f=b[d](a);if(f!==null)return f}return"string"}function A(a){for(var b=0;b<D.length;b++)if(D[b].nTable==a)return D[b];return null}function ca(a){for(var b=[],c=a.aoData.length,d=0;d<c;d++)b.push(a.aoData[d]._aData);return b}function ba(a){for(var b=[],c=0,d=a.aoData.length;c<d;c++)a.aoData[c].nTr!==null&&b.push(a.aoData[c].nTr);
return b}function Q(a,b){var c=[],d,f,e,h,j;f=0;var k=a.aoData.length;if(typeof b!="undefined"){f=b;k=b+1}for(f=f;f<k;f++){j=a.aoData[f];if(j.nTr!==null){b=[];e=0;for(h=j.nTr.childNodes.length;e<h;e++){d=j.nTr.childNodes[e].nodeName.toLowerCase();if(d=="td"||d=="th")b.push(j.nTr.childNodes[e])}e=d=0;for(h=a.aoColumns.length;e<h;e++)if(a.aoColumns[e].bVisible)c.push(b[e-d]);else{c.push(j._anHidden[e]);d++}}}return c}function sa(a){return a.replace(new RegExp("(\\/|\\.|\\*|\\+|\\?|\\||\\(|\\)|\\[|\\]|\\{|\\}|\\\\|\\$|\\^)",
"g"),"\\$1")}function ua(a,b){for(var c=-1,d=0,f=a.length;d<f;d++)if(a[d]==b)c=d;else a[d]>b&&a[d]--;c!=-1&&a.splice(c,1)}function Fa(a,b){b=b.split(",");for(var c=[],d=0,f=a.aoColumns.length;d<f;d++)for(var e=0;e<f;e++)if(a.aoColumns[d].sName==b[e]){c.push(e);break}return c}function ka(a){for(var b="",c=0,d=a.aoColumns.length;c<d;c++)b+=a.aoColumns[c].sName+",";if(b.length==d)return"";return b.slice(0,-1)}function J(a,b,c){a=a.sTableId===""?"DataTables warning: "+c:"DataTables warning (table id = '"+
a.sTableId+"'): "+c;if(b===0)if(n.sErrMode=="alert")alert(a);else throw a;else typeof console!="undefined"&&typeof console.log!="undefined"&&console.log(a)}function la(a){a.aoData.splice(0,a.aoData.length);a.aiDisplayMaster.splice(0,a.aiDisplayMaster.length);a.aiDisplay.splice(0,a.aiDisplay.length);E(a)}function va(a){if(!(!a.oFeatures.bStateSave||typeof a.bDestroying!="undefined")){var b,c,d,f="{";f+='"iCreate":'+(new Date).getTime()+",";f+='"iStart":'+(a.oScroll.bInfinite?0:a._iDisplayStart)+",";
f+='"iEnd":'+(a.oScroll.bInfinite?a._iDisplayLength:a._iDisplayEnd)+",";f+='"iLength":'+a._iDisplayLength+",";f+='"sFilter":"'+encodeURIComponent(a.oPreviousSearch.sSearch)+'",';f+='"sFilterEsc":'+!a.oPreviousSearch.bRegex+",";f+='"aaSorting":[ ';for(b=0;b<a.aaSorting.length;b++)f+="["+a.aaSorting[b][0]+',"'+a.aaSorting[b][1]+'"],';f=f.substring(0,f.length-1);f+="],";f+='"aaSearchCols":[ ';for(b=0;b<a.aoPreSearchCols.length;b++)f+='["'+encodeURIComponent(a.aoPreSearchCols[b].sSearch)+'",'+!a.aoPreSearchCols[b].bRegex+
"],";f=f.substring(0,f.length-1);f+="],";f+='"abVisCols":[ ';for(b=0;b<a.aoColumns.length;b++)f+=a.aoColumns[b].bVisible+",";f=f.substring(0,f.length-1);f+="]";b=0;for(c=a.aoStateSave.length;b<c;b++){d=a.aoStateSave[b].fn(a,f);if(d!=="")f=d}f+="}";Wa(a.sCookiePrefix+a.sInstance,f,a.iCookieDuration,a.sCookiePrefix,a.fnCookieCallback)}}function Xa(a,b){if(a.oFeatures.bStateSave){var c,d,f;d=wa(a.sCookiePrefix+a.sInstance);if(d!==null&&d!==""){try{c=typeof i.parseJSON=="function"?i.parseJSON(d.replace(/'/g,
'"')):eval("("+d+")")}catch(e){return}d=0;for(f=a.aoStateLoad.length;d<f;d++)if(!a.aoStateLoad[d].fn(a,c))return;a.oLoadedState=i.extend(true,{},c);a._iDisplayStart=c.iStart;a.iInitDisplayStart=c.iStart;a._iDisplayEnd=c.iEnd;a._iDisplayLength=c.iLength;a.oPreviousSearch.sSearch=decodeURIComponent(c.sFilter);a.aaSorting=c.aaSorting.slice();a.saved_aaSorting=c.aaSorting.slice();if(typeof c.sFilterEsc!="undefined")a.oPreviousSearch.bRegex=!c.sFilterEsc;if(typeof c.aaSearchCols!="undefined")for(d=0;d<
c.aaSearchCols.length;d++)a.aoPreSearchCols[d]={sSearch:decodeURIComponent(c.aaSearchCols[d][0]),bRegex:!c.aaSearchCols[d][1]};if(typeof c.abVisCols!="undefined"){b.saved_aoColumns=[];for(d=0;d<c.abVisCols.length;d++){b.saved_aoColumns[d]={};b.saved_aoColumns[d].bVisible=c.abVisCols[d]}}}}}function Wa(a,b,c,d,f){var e=new Date;e.setTime(e.getTime()+c*1E3);c=za.location.pathname.split("/");a=a+"_"+c.pop().replace(/[\/:]/g,"").toLowerCase();var h;if(f!==null){h=typeof i.parseJSON=="function"?i.parseJSON(b):
eval("("+b+")");b=f(a,h,e.toGMTString(),c.join("/")+"/")}else b=a+"="+encodeURIComponent(b)+"; expires="+e.toGMTString()+"; path="+c.join("/")+"/";f="";e=9999999999999;if((wa(a)!==null?p.cookie.length:b.length+p.cookie.length)+10>4096){a=p.cookie.split(";");for(var j=0,k=a.length;j<k;j++)if(a[j].indexOf(d)!=-1){var m=a[j].split("=");try{h=eval("("+decodeURIComponent(m[1])+")")}catch(u){continue}if(typeof h.iCreate!="undefined"&&h.iCreate<e){f=m[0];e=h.iCreate}}if(f!=="")p.cookie=f+"=; expires=Thu, 01-Jan-1970 00:00:01 GMT; path="+
c.join("/")+"/"}p.cookie=b}function wa(a){var b=za.location.pathname.split("/");a=a+"_"+b[b.length-1].replace(/[\/:]/g,"").toLowerCase()+"=";b=p.cookie.split(";");for(var c=0;c<b.length;c++){for(var d=b[c];d.charAt(0)==" ";)d=d.substring(1,d.length);if(d.indexOf(a)===0)return decodeURIComponent(d.substring(a.length,d.length))}return null}function Y(a,b){b=i(b).children("tr");var c,d,f,e,h,j,k,m,u=function(L,T,B){for(;typeof L[T][B]!="undefined";)B++;return B};a.splice(0,a.length);d=0;for(j=b.length;d<
j;d++)a.push([]);d=0;for(j=b.length;d<j;d++){f=0;for(k=b[d].childNodes.length;f<k;f++){c=b[d].childNodes[f];if(c.nodeName.toUpperCase()=="TD"||c.nodeName.toUpperCase()=="TH"){var r=c.getAttribute("colspan")*1,H=c.getAttribute("rowspan")*1;r=!r||r===0||r===1?1:r;H=!H||H===0||H===1?1:H;m=u(a,d,0);for(h=0;h<r;h++)for(e=0;e<H;e++){a[d+e][m+h]={cell:c,unique:r==1?true:false};a[d+e].nTr=b[d]}}}}}function S(a,b,c){var d=[];if(typeof c=="undefined"){c=a.aoHeader;if(typeof b!="undefined"){c=[];Y(c,b)}}b=0;
for(var f=c.length;b<f;b++)for(var e=0,h=c[b].length;e<h;e++)if(c[b][e].unique&&(typeof d[e]=="undefined"||!a.bSortCellsTop))d[e]=c[b][e].cell;return d}function Ya(){var a=p.createElement("p"),b=a.style;b.width="100%";b.height="200px";b.padding="0px";var c=p.createElement("div");b=c.style;b.position="absolute";b.top="0px";b.left="0px";b.visibility="hidden";b.width="200px";b.height="150px";b.padding="0px";b.overflow="hidden";c.appendChild(a);p.body.appendChild(c);b=a.offsetWidth;c.style.overflow="scroll";
a=a.offsetWidth;if(b==a)a=c.clientWidth;p.body.removeChild(c);return b-a}function P(a,b,c){for(var d=0,f=b.length;d<f;d++)for(var e=0,h=b[d].childNodes.length;e<h;e++)if(b[d].childNodes[e].nodeType==1)typeof c!="undefined"?a(b[d].childNodes[e],c[d].childNodes[e]):a(b[d].childNodes[e])}function o(a,b,c,d){if(typeof d=="undefined")d=c;if(typeof b[c]!="undefined")a[d]=b[c]}function fa(a,b,c){for(var d=[],f=0,e=a.aoColumns.length;f<e;f++)d.push(G(a,b,f,c));return d}function G(a,b,c,d){var f=a.aoColumns[c];
if((c=f.fnGetData(a.aoData[b]._aData))===undefined){if(a.iDrawError!=a.iDraw&&f.sDefaultContent===null){J(a,0,"Requested unknown parameter '"+f.mDataProp+"' from the data source for row "+b);a.iDrawError=a.iDraw}return f.sDefaultContent}if(c===null&&f.sDefaultContent!==null)c=f.sDefaultContent;else if(typeof c=="function")return c();if(d=="display"&&c===null)return"";return c}function O(a,b,c,d){a.aoColumns[c].fnSetData(a.aoData[b]._aData,d)}function aa(a){if(a===null)return function(){return null};
else if(typeof a=="function")return function(c){return a(c)};else if(typeof a=="string"&&a.indexOf(".")!=-1){var b=a.split(".");return b.length==2?function(c){return c[b[0]][b[1]]}:b.length==3?function(c){return c[b[0]][b[1]][b[2]]}:function(c){for(var d=0,f=b.length;d<f;d++)c=c[b[d]];return c}}else return function(c){return c[a]}}function Ba(a){if(a===null)return function(){};else if(typeof a=="function")return function(c,d){return a(c,d)};else if(typeof a=="string"&&a.indexOf(".")!=-1){var b=a.split(".");
return b.length==2?function(c,d){c[b[0]][b[1]]=d}:b.length==3?function(c,d){c[b[0]][b[1]][b[2]]=d}:function(c,d){for(var f=0,e=b.length-1;f<e;f++)c=c[b[f]];c[b[b.length-1]]=d}}else return function(c,d){c[a]=d}}this.oApi={};this.fnDraw=function(a){var b=A(this[n.iApiIndex]);if(typeof a!="undefined"&&a===false){E(b);C(b)}else da(b)};this.fnFilter=function(a,b,c,d,f){var e=A(this[n.iApiIndex]);if(e.oFeatures.bFilter){if(typeof c=="undefined")c=false;if(typeof d=="undefined")d=true;if(typeof f=="undefined")f=
true;if(typeof b=="undefined"||b===null){N(e,{sSearch:a,bRegex:c,bSmart:d},1);if(f&&typeof e.aanFeatures.f!="undefined"){b=e.aanFeatures.f;c=0;for(d=b.length;c<d;c++)i("input",b[c]).val(a)}}else{e.aoPreSearchCols[b].sSearch=a;e.aoPreSearchCols[b].bRegex=c;e.aoPreSearchCols[b].bSmart=d;N(e,e.oPreviousSearch,1)}}};this.fnSettings=function(){return A(this[n.iApiIndex])};this.fnVersionCheck=n.fnVersionCheck;this.fnSort=function(a){var b=A(this[n.iApiIndex]);b.aaSorting=a;R(b)};this.fnSortListener=function(a,
b,c){ja(A(this[n.iApiIndex]),a,b,c)};this.fnAddData=function(a,b){if(a.length===0)return[];var c=[],d,f=A(this[n.iApiIndex]);if(typeof a[0]=="object")for(var e=0;e<a.length;e++){d=v(f,a[e]);if(d==-1)return c;c.push(d)}else{d=v(f,a);if(d==-1)return c;c.push(d)}f.aiDisplay=f.aiDisplayMaster.slice();if(typeof b=="undefined"||b)da(f);return c};this.fnDeleteRow=function(a,b,c){var d=A(this[n.iApiIndex]);a=typeof a=="object"?W(d,a):a;var f=d.aoData.splice(a,1),e=i.inArray(a,d.aiDisplay);d.asDataSearch.splice(e,
1);ua(d.aiDisplayMaster,a);ua(d.aiDisplay,a);typeof b=="function"&&b.call(this,d,f);if(d._iDisplayStart>=d.aiDisplay.length){d._iDisplayStart-=d._iDisplayLength;if(d._iDisplayStart<0)d._iDisplayStart=0}if(typeof c=="undefined"||c){E(d);C(d)}return f};this.fnClearTable=function(a){var b=A(this[n.iApiIndex]);la(b);if(typeof a=="undefined"||a)C(b)};this.fnOpen=function(a,b,c){var d=A(this[n.iApiIndex]);this.fnClose(a);var f=p.createElement("tr"),e=p.createElement("td");f.appendChild(e);e.className=c;
e.colSpan=Z(d);if(typeof b.jquery!="undefined"||typeof b=="object")e.appendChild(b);else e.innerHTML=b;b=i("tr",d.nTBody);i.inArray(a,b)!=-1&&i(f).insertAfter(a);d.aoOpenRows.push({nTr:f,nParent:a});return f};this.fnClose=function(a){for(var b=A(this[n.iApiIndex]),c=0;c<b.aoOpenRows.length;c++)if(b.aoOpenRows[c].nParent==a){(a=b.aoOpenRows[c].nTr.parentNode)&&a.removeChild(b.aoOpenRows[c].nTr);b.aoOpenRows.splice(c,1);return 0}return 1};this.fnGetData=function(a,b){var c=A(this[n.iApiIndex]);if(typeof a!=
"undefined"){a=typeof a=="object"?W(c,a):a;if(typeof b!="undefined")return G(c,a,b,"");return typeof c.aoData[a]!="undefined"?c.aoData[a]._aData:null}return ca(c)};this.fnGetNodes=function(a){var b=A(this[n.iApiIndex]);if(typeof a!="undefined")return typeof b.aoData[a]!="undefined"?b.aoData[a].nTr:null;return ba(b)};this.fnGetPosition=function(a){var b=A(this[n.iApiIndex]),c=a.nodeName.toUpperCase();if(c=="TR")return W(b,a);else if(c=="TD"||c=="TH"){c=W(b,a.parentNode);for(var d=Q(b,c),f=0;f<b.aoColumns.length;f++)if(d[f]==
a)return[c,ta(b,f),f]}return null};this.fnUpdate=function(a,b,c,d,f){var e=A(this[n.iApiIndex]);b=typeof b=="object"?W(e,b):b;if(i.isArray(a)&&typeof a=="object"){e.aoData[b]._aData=a.slice();for(c=0;c<e.aoColumns.length;c++)this.fnUpdate(G(e,b,c),b,c,false,false)}else if(a!==null&&typeof a=="object"){e.aoData[b]._aData=i.extend(true,{},a);for(c=0;c<e.aoColumns.length;c++)this.fnUpdate(G(e,b,c),b,c,false,false)}else{a=a;O(e,b,c,a);if(e.aoColumns[c].fnRender!==null){a=e.aoColumns[c].fnRender({iDataRow:b,
iDataColumn:c,aData:e.aoData[b]._aData,oSettings:e});e.aoColumns[c].bUseRendered&&O(e,b,c,a)}if(e.aoData[b].nTr!==null)Q(e,b)[c].innerHTML=a}c=i.inArray(b,e.aiDisplay);e.asDataSearch[c]=ra(e,fa(e,b,"filter"));if(typeof f=="undefined"||f)ea(e);if(typeof d=="undefined"||d)da(e);return 0};this.fnSetColumnVis=function(a,b,c){var d=A(this[n.iApiIndex]),f,e;e=d.aoColumns.length;var h,j;if(d.aoColumns[a].bVisible!=b){if(b){for(f=j=0;f<a;f++)d.aoColumns[f].bVisible&&j++;j=j>=Z(d);if(!j)for(f=a;f<e;f++)if(d.aoColumns[f].bVisible){h=
f;break}f=0;for(e=d.aoData.length;f<e;f++)if(d.aoData[f].nTr!==null)j?d.aoData[f].nTr.appendChild(d.aoData[f]._anHidden[a]):d.aoData[f].nTr.insertBefore(d.aoData[f]._anHidden[a],Q(d,f)[h])}else{f=0;for(e=d.aoData.length;f<e;f++)if(d.aoData[f].nTr!==null){h=Q(d,f)[a];d.aoData[f]._anHidden[a]=h;h.parentNode.removeChild(h)}}d.aoColumns[a].bVisible=b;M(d,d.aoHeader);d.nTFoot&&M(d,d.aoFooter);f=0;for(e=d.aoOpenRows.length;f<e;f++)d.aoOpenRows[f].nTr.colSpan=Z(d);if(typeof c=="undefined"||c){ea(d);C(d)}va(d)}};
this.fnPageChange=function(a,b){var c=A(this[n.iApiIndex]);ma(c,a);E(c);if(typeof b=="undefined"||b)C(c)};this.fnDestroy=function(){var a=A(this[n.iApiIndex]),b=a.nTableWrapper.parentNode,c=a.nTBody,d,f;a.bDestroying=true;d=0;for(f=a.aoDestroyCallback.length;d<f;d++)a.aoDestroyCallback[d].fn();d=0;for(f=a.aoColumns.length;d<f;d++)a.aoColumns[d].bVisible===false&&this.fnSetColumnVis(d,true);i(a.nTableWrapper).find("*").andSelf().unbind(".DT");i("tbody>tr>td."+a.oClasses.sRowEmpty,a.nTable).parent().remove();
if(a.nTable!=a.nTHead.parentNode){i(a.nTable).children("thead").remove();a.nTable.appendChild(a.nTHead)}if(a.nTFoot&&a.nTable!=a.nTFoot.parentNode){i(a.nTable).children("tfoot").remove();a.nTable.appendChild(a.nTFoot)}a.nTable.parentNode.removeChild(a.nTable);i(a.nTableWrapper).remove();a.aaSorting=[];a.aaSortingFixed=[];V(a);i(ba(a)).removeClass(a.asStripeClasses.join(" "));if(a.bJUI){i("th",a.nTHead).removeClass([n.oStdClasses.sSortable,n.oJUIClasses.sSortableAsc,n.oJUIClasses.sSortableDesc,n.oJUIClasses.sSortableNone].join(" "));
i("th span."+n.oJUIClasses.sSortIcon,a.nTHead).remove();i("th",a.nTHead).each(function(){var e=i("div."+n.oJUIClasses.sSortJUIWrapper,this),h=e.contents();i(this).append(h);e.remove()})}else i("th",a.nTHead).removeClass([n.oStdClasses.sSortable,n.oStdClasses.sSortableAsc,n.oStdClasses.sSortableDesc,n.oStdClasses.sSortableNone].join(" "));a.nTableReinsertBefore?b.insertBefore(a.nTable,a.nTableReinsertBefore):b.appendChild(a.nTable);d=0;for(f=a.aoData.length;d<f;d++)a.aoData[d].nTr!==null&&c.appendChild(a.aoData[d].nTr);
if(a.oFeatures.bAutoWidth===true)a.nTable.style.width=q(a.sDestroyWidth);i(c).children("tr:even").addClass(a.asDestroyStripes[0]);i(c).children("tr:odd").addClass(a.asDestroyStripes[1]);d=0;for(f=D.length;d<f;d++)D[d]==a&&D.splice(d,1);a=null};this.fnAdjustColumnSizing=function(a){var b=A(this[n.iApiIndex]);ea(b);if(typeof a=="undefined"||a)this.fnDraw(false);else if(b.oScroll.sX!==""||b.oScroll.sY!=="")this.oApi._fnScrollDraw(b)};for(var xa in n.oApi)if(xa)this[xa]=s(xa);this.oApi._fnExternApiFunc=
s;this.oApi._fnInitialise=t;this.oApi._fnInitComplete=w;this.oApi._fnLanguageProcess=y;this.oApi._fnAddColumn=F;this.oApi._fnColumnOptions=x;this.oApi._fnAddData=v;this.oApi._fnCreateTr=z;this.oApi._fnGatherData=$;this.oApi._fnBuildHead=X;this.oApi._fnDrawHead=M;this.oApi._fnDraw=C;this.oApi._fnReDraw=da;this.oApi._fnAjaxUpdate=Ca;this.oApi._fnAjaxParameters=Da;this.oApi._fnAjaxUpdateDraw=Ea;this.oApi._fnServerParams=ha;this.oApi._fnAddOptionsHtml=Aa;this.oApi._fnFeatureHtmlTable=Ja;this.oApi._fnScrollDraw=
Ma;this.oApi._fnAdjustColumnSizing=ea;this.oApi._fnFeatureHtmlFilter=Ha;this.oApi._fnFilterComplete=N;this.oApi._fnFilterCustom=Qa;this.oApi._fnFilterColumn=Pa;this.oApi._fnFilter=Oa;this.oApi._fnBuildSearchArray=oa;this.oApi._fnBuildSearchRow=ra;this.oApi._fnFilterCreateSearch=pa;this.oApi._fnDataToSearch=qa;this.oApi._fnSort=R;this.oApi._fnSortAttachListener=ja;this.oApi._fnSortingClasses=V;this.oApi._fnFeatureHtmlPaginate=La;this.oApi._fnPageChange=ma;this.oApi._fnFeatureHtmlInfo=Ka;this.oApi._fnUpdateInfo=
Ra;this.oApi._fnFeatureHtmlLength=Ga;this.oApi._fnFeatureHtmlProcessing=Ia;this.oApi._fnProcessingDisplay=K;this.oApi._fnVisibleToColumnIndex=Na;this.oApi._fnColumnIndexToVisible=ta;this.oApi._fnNodeToDataIndex=W;this.oApi._fnVisbleColumns=Z;this.oApi._fnCalculateEnd=E;this.oApi._fnConvertToWidth=Sa;this.oApi._fnCalculateColumnWidths=ga;this.oApi._fnScrollingWidthAdjust=Ua;this.oApi._fnGetWidestNode=Ta;this.oApi._fnGetMaxLenString=Va;this.oApi._fnStringToCss=q;this.oApi._fnArrayCmp=Za;this.oApi._fnDetectType=
ia;this.oApi._fnSettingsFromNode=A;this.oApi._fnGetDataMaster=ca;this.oApi._fnGetTrNodes=ba;this.oApi._fnGetTdNodes=Q;this.oApi._fnEscapeRegex=sa;this.oApi._fnDeleteIndex=ua;this.oApi._fnReOrderIndex=Fa;this.oApi._fnColumnOrdering=ka;this.oApi._fnLog=J;this.oApi._fnClearTable=la;this.oApi._fnSaveState=va;this.oApi._fnLoadState=Xa;this.oApi._fnCreateCookie=Wa;this.oApi._fnReadCookie=wa;this.oApi._fnDetectHeader=Y;this.oApi._fnGetUniqueThs=S;this.oApi._fnScrollBarWidth=Ya;this.oApi._fnApplyToChildren=
P;this.oApi._fnMap=o;this.oApi._fnGetRowData=fa;this.oApi._fnGetCellData=G;this.oApi._fnSetCellData=O;this.oApi._fnGetObjectDataFn=aa;this.oApi._fnSetObjectDataFn=Ba;var ya=this;return this.each(function(){var a=0,b,c,d,f;a=0;for(b=D.length;a<b;a++){if(D[a].nTable==this)if(typeof g=="undefined"||typeof g.bRetrieve!="undefined"&&g.bRetrieve===true)return D[a].oInstance;else if(typeof g.bDestroy!="undefined"&&g.bDestroy===true){D[a].oInstance.fnDestroy();break}else{J(D[a],0,"Cannot reinitialise DataTable.\n\nTo retrieve the DataTables object for this table, please pass either no arguments to the dataTable() function, or set bRetrieve to true. Alternatively, to destory the old table and create a new one, set bDestroy to true (note that a lot of changes to the configuration can be made through the API which is usually much faster).");
return}if(D[a].sTableId!==""&&D[a].sTableId==this.getAttribute("id")){D.splice(a,1);break}}var e=new l;D.push(e);var h=false,j=false;a=this.getAttribute("id");if(a!==null){e.sTableId=a;e.sInstance=a}else e.sInstance=n._oExternConfig.iNextUnique++;if(this.nodeName.toLowerCase()!="table")J(e,0,"Attempted to initialise DataTables on a node which is not a table: "+this.nodeName);else{e.nTable=this;e.oInstance=ya.length==1?ya:i(this).dataTable();e.oApi=ya.oApi;e.sDestroyWidth=i(this).width();if(typeof g!=
"undefined"&&g!==null){e.oInit=g;o(e.oFeatures,g,"bPaginate");o(e.oFeatures,g,"bLengthChange");o(e.oFeatures,g,"bFilter");o(e.oFeatures,g,"bSort");o(e.oFeatures,g,"bInfo");o(e.oFeatures,g,"bProcessing");o(e.oFeatures,g,"bAutoWidth");o(e.oFeatures,g,"bSortClasses");o(e.oFeatures,g,"bServerSide");o(e.oFeatures,g,"bDeferRender");o(e.oScroll,g,"sScrollX","sX");o(e.oScroll,g,"sScrollXInner","sXInner");o(e.oScroll,g,"sScrollY","sY");o(e.oScroll,g,"bScrollCollapse","bCollapse");o(e.oScroll,g,"bScrollInfinite",
"bInfinite");o(e.oScroll,g,"iScrollLoadGap","iLoadGap");o(e.oScroll,g,"bScrollAutoCss","bAutoCss");o(e,g,"asStripClasses","asStripeClasses");o(e,g,"asStripeClasses");o(e,g,"fnPreDrawCallback");o(e,g,"fnRowCallback");o(e,g,"fnHeaderCallback");o(e,g,"fnFooterCallback");o(e,g,"fnCookieCallback");o(e,g,"fnInitComplete");o(e,g,"fnServerData");o(e,g,"fnFormatNumber");o(e,g,"aaSorting");o(e,g,"aaSortingFixed");o(e,g,"aLengthMenu");o(e,g,"sPaginationType");o(e,g,"sAjaxSource");o(e,g,"sAjaxDataProp");o(e,
g,"iCookieDuration");o(e,g,"sCookiePrefix");o(e,g,"sDom");o(e,g,"bSortCellsTop");o(e,g,"oSearch","oPreviousSearch");o(e,g,"aoSearchCols","aoPreSearchCols");o(e,g,"iDisplayLength","_iDisplayLength");o(e,g,"bJQueryUI","bJUI");o(e.oLanguage,g,"fnInfoCallback");typeof g.fnDrawCallback=="function"&&e.aoDrawCallback.push({fn:g.fnDrawCallback,sName:"user"});typeof g.fnServerParams=="function"&&e.aoServerParams.push({fn:g.fnServerParams,sName:"user"});typeof g.fnStateSaveCallback=="function"&&e.aoStateSave.push({fn:g.fnStateSaveCallback,
sName:"user"});typeof g.fnStateLoadCallback=="function"&&e.aoStateLoad.push({fn:g.fnStateLoadCallback,sName:"user"});if(e.oFeatures.bServerSide&&e.oFeatures.bSort&&e.oFeatures.bSortClasses)e.aoDrawCallback.push({fn:V,sName:"server_side_sort_classes"});else e.oFeatures.bDeferRender&&e.aoDrawCallback.push({fn:V,sName:"defer_sort_classes"});if(typeof g.bJQueryUI!="undefined"&&g.bJQueryUI){e.oClasses=n.oJUIClasses;if(typeof g.sDom=="undefined")e.sDom='<"H"lfr>t<"F"ip>'}if(e.oScroll.sX!==""||e.oScroll.sY!==
"")e.oScroll.iBarWidth=Ya();if(typeof g.iDisplayStart!="undefined"&&typeof e.iInitDisplayStart=="undefined"){e.iInitDisplayStart=g.iDisplayStart;e._iDisplayStart=g.iDisplayStart}if(typeof g.bStateSave!="undefined"){e.oFeatures.bStateSave=g.bStateSave;Xa(e,g);e.aoDrawCallback.push({fn:va,sName:"state_save"})}if(typeof g.iDeferLoading!="undefined"){e.bDeferLoading=true;e._iRecordsTotal=g.iDeferLoading;e._iRecordsDisplay=g.iDeferLoading}if(typeof g.aaData!="undefined")j=true;if(typeof g!="undefined"&&
typeof g.aoData!="undefined")g.aoColumns=g.aoData;if(typeof g.oLanguage!="undefined")if(typeof g.oLanguage.sUrl!="undefined"&&g.oLanguage.sUrl!==""){e.oLanguage.sUrl=g.oLanguage.sUrl;i.getJSON(e.oLanguage.sUrl,null,function(u){y(e,u,true)});h=true}else y(e,g.oLanguage,false)}else g={};if(typeof g.asStripClasses=="undefined"&&typeof g.asStripeClasses=="undefined"){e.asStripeClasses.push(e.oClasses.sStripeOdd);e.asStripeClasses.push(e.oClasses.sStripeEven)}c=false;d=i(this).children("tbody").children("tr");
a=0;for(b=e.asStripeClasses.length;a<b;a++)if(d.filter(":lt(2)").hasClass(e.asStripeClasses[a])){c=true;break}if(c){e.asDestroyStripes=["",""];if(i(d[0]).hasClass(e.oClasses.sStripeOdd))e.asDestroyStripes[0]+=e.oClasses.sStripeOdd+" ";if(i(d[0]).hasClass(e.oClasses.sStripeEven))e.asDestroyStripes[0]+=e.oClasses.sStripeEven;if(i(d[1]).hasClass(e.oClasses.sStripeOdd))e.asDestroyStripes[1]+=e.oClasses.sStripeOdd+" ";if(i(d[1]).hasClass(e.oClasses.sStripeEven))e.asDestroyStripes[1]+=e.oClasses.sStripeEven;
d.removeClass(e.asStripeClasses.join(" "))}c=[];var k;a=this.getElementsByTagName("thead");if(a.length!==0){Y(e.aoHeader,a[0]);c=S(e)}if(typeof g.aoColumns=="undefined"){k=[];a=0;for(b=c.length;a<b;a++)k.push(null)}else k=g.aoColumns;a=0;for(b=k.length;a<b;a++){if(typeof g.saved_aoColumns!="undefined"&&g.saved_aoColumns.length==b){if(k[a]===null)k[a]={};k[a].bVisible=g.saved_aoColumns[a].bVisible}F(e,c?c[a]:null)}if(typeof g.aoColumnDefs!="undefined")for(a=g.aoColumnDefs.length-1;a>=0;a--){var m=
g.aoColumnDefs[a].aTargets;i.isArray(m)||J(e,1,"aTargets must be an array of targets, not a "+typeof m);c=0;for(d=m.length;c<d;c++)if(typeof m[c]=="number"&&m[c]>=0){for(;e.aoColumns.length<=m[c];)F(e);x(e,m[c],g.aoColumnDefs[a])}else if(typeof m[c]=="number"&&m[c]<0)x(e,e.aoColumns.length+m[c],g.aoColumnDefs[a]);else if(typeof m[c]=="string"){b=0;for(f=e.aoColumns.length;b<f;b++)if(m[c]=="_all"||i(e.aoColumns[b].nTh).hasClass(m[c]))x(e,b,g.aoColumnDefs[a])}}if(typeof k!="undefined"){a=0;for(b=k.length;a<
b;a++)x(e,a,k[a])}a=0;for(b=e.aaSorting.length;a<b;a++){if(e.aaSorting[a][0]>=e.aoColumns.length)e.aaSorting[a][0]=0;k=e.aoColumns[e.aaSorting[a][0]];if(typeof e.aaSorting[a][2]=="undefined")e.aaSorting[a][2]=0;if(typeof g.aaSorting=="undefined"&&typeof e.saved_aaSorting=="undefined")e.aaSorting[a][1]=k.asSorting[0];c=0;for(d=k.asSorting.length;c<d;c++)if(e.aaSorting[a][1]==k.asSorting[c]){e.aaSorting[a][2]=c;break}}V(e);a=i(this).children("thead");if(a.length===0){a=[p.createElement("thead")];this.appendChild(a[0])}e.nTHead=
a[0];a=i(this).children("tbody");if(a.length===0){a=[p.createElement("tbody")];this.appendChild(a[0])}e.nTBody=a[0];a=i(this).children("tfoot");if(a.length>0){e.nTFoot=a[0];Y(e.aoFooter,e.nTFoot)}if(j)for(a=0;a<g.aaData.length;a++)v(e,g.aaData[a]);else $(e);e.aiDisplay=e.aiDisplayMaster.slice();e.bInitialised=true;h===false&&t(e)}})}})(jQuery,window,document);
/*!
 * jQuery Form Plugin
 * version: 2.87 (20-OCT-2011)
 * @requires jQuery v1.3.2 or later
 *
 * Examples and documentation at: http://malsup.com/jquery/form/
 * Dual licensed under the MIT and GPL licenses:
 *   http://www.opensource.org/licenses/mit-license.php
 *   http://www.gnu.org/licenses/gpl.html
 */
;(function($) {

/*
	Usage Note:
	-----------
	Do not use both ajaxSubmit and ajaxForm on the same form.  These
	functions are intended to be exclusive.  Use ajaxSubmit if you want
	to bind your own submit handler to the form.  For example,

	$(document).ready(function() {
		$('#myForm').bind('submit', function(e) {
			e.preventDefault(); // <-- important
			$(this).ajaxSubmit({
				target: '#output'
			});
		});
	});

	Use ajaxForm when you want the plugin to manage all the event binding
	for you.  For example,

	$(document).ready(function() {
		$('#myForm').ajaxForm({
			target: '#output'
		});
	});

	When using ajaxForm, the ajaxSubmit function will be invoked for you
	at the appropriate time.
*/

/**
 * ajaxSubmit() provides a mechanism for immediately submitting
 * an HTML form using AJAX.
 */
$.fn.ajaxSubmit = function(options) {
	// fast fail if nothing selected (http://dev.jquery.com/ticket/2752)
	if (!this.length) {
		log('ajaxSubmit: skipping submit process - no element selected');
		return this;
	}
	
	var method, action, url, $form = this;

	if (typeof options == 'function') {
		options = { success: options };
	}

	method = this.attr('method');
	action = this.attr('action');
	url = (typeof action === 'string') ? $.trim(action) : '';
	url = url || window.location.href || '';
	if (url) {
		// clean url (don't include hash vaue)
		url = (url.match(/^([^#]+)/)||[])[1];
	}

	options = $.extend(true, {
		url:  url,
		success: $.ajaxSettings.success,
		type: method || 'GET',
		iframeSrc: /^https/i.test(window.location.href || '') ? 'javascript:false' : 'about:blank'
	}, options);

	// hook for manipulating the form data before it is extracted;
	// convenient for use with rich editors like tinyMCE or FCKEditor
	var veto = {};
	this.trigger('form-pre-serialize', [this, options, veto]);
	if (veto.veto) {
		log('ajaxSubmit: submit vetoed via form-pre-serialize trigger');
		return this;
	}

	// provide opportunity to alter form data before it is serialized
	if (options.beforeSerialize && options.beforeSerialize(this, options) === false) {
		log('ajaxSubmit: submit aborted via beforeSerialize callback');
		return this;
	}

   var traditional = options.traditional;
   if ( traditional === undefined ) {
      traditional = $.ajaxSettings.traditional;
   }
   
	var qx,n,v,a = this.formToArray(options.semantic);
	if (options.data) {
		options.extraData = options.data;
      qx = $.param(options.data, traditional);
	}

	// give pre-submit callback an opportunity to abort the submit
	if (options.beforeSubmit && options.beforeSubmit(a, this, options) === false) {
		log('ajaxSubmit: submit aborted via beforeSubmit callback');
		return this;
	}

	// fire vetoable 'validate' event
	this.trigger('form-submit-validate', [a, this, options, veto]);
	if (veto.veto) {
		log('ajaxSubmit: submit vetoed via form-submit-validate trigger');
		return this;
	}

	var q = $.param(a, traditional);
   if (qx)
      q = ( q ? (q + '&' + qx) : qx );

	if (options.type.toUpperCase() == 'GET') {
		options.url += (options.url.indexOf('?') >= 0 ? '&' : '?') + q;
		options.data = null;  // data is null for 'get'
	}
	else {
		options.data = q; // data is the query string for 'post'
	}

	var callbacks = [];
	if (options.resetForm) {
		callbacks.push(function() { $form.resetForm(); });
	}
	if (options.clearForm) {
		callbacks.push(function() { $form.clearForm(options.includeHidden); });
	}

	// perform a load on the target only if dataType is not provided
	if (!options.dataType && options.target) {
		var oldSuccess = options.success || function(){};
		callbacks.push(function(data) {
			var fn = options.replaceTarget ? 'replaceWith' : 'html';
			$(options.target)[fn](data).each(oldSuccess, arguments);
		});
	}
	else if (options.success) {
		callbacks.push(options.success);
	}

	options.success = function(data, status, xhr) { // jQuery 1.4+ passes xhr as 3rd arg
		var context = options.context || options;   // jQuery 1.4+ supports scope context 
		for (var i=0, max=callbacks.length; i < max; i++) {
			callbacks[i].apply(context, [data, status, xhr || $form, $form]);
		}
	};

	// are there files to upload?
	var fileInputs = $('input:file', this).length > 0;
	var mp = 'multipart/form-data';
	var multipart = ($form.attr('enctype') == mp || $form.attr('encoding') == mp);

	// options.iframe allows user to force iframe mode
	// 06-NOV-09: now defaulting to iframe mode if file input is detected
   if (options.iframe !== false && (fileInputs || options.iframe || multipart)) {
	   // hack to fix Safari hang (thanks to Tim Molendijk for this)
	   // see:  http://groups.google.com/group/jquery-dev/browse_thread/thread/36395b7ab510dd5d
	   if (options.closeKeepAlive) {
		   $.get(options.closeKeepAlive, function() { fileUpload(a); });
		}
	   else {
		   fileUpload(a);
		}
   }
   else {
		// IE7 massage (see issue 57)
		if ($.browser.msie && method == 'get' && typeof options.type === "undefined") {
			var ieMeth = $form[0].getAttribute('method');
			if (typeof ieMeth === 'string')
				options.type = ieMeth;
		}
		$.ajax(options);
   }

	// fire 'notify' event
	this.trigger('form-submit-notify', [this, options]);
	return this;


	// private function for handling file uploads (hat tip to YAHOO!)
	function fileUpload(a) {
		var form = $form[0], el, i, s, g, id, $io, io, xhr, sub, n, timedOut, timeoutHandle;
        var useProp = !!$.fn.prop;

        if (a) {
            if ( useProp ) {
            	// ensure that every serialized input is still enabled
              	for (i=0; i < a.length; i++) {
                    el = $(form[a[i].name]);
                    el.prop('disabled', false);
              	}
            } else {
              	for (i=0; i < a.length; i++) {
                    el = $(form[a[i].name]);
                    el.removeAttr('disabled');
              	}
            };
        }

		if ($(':input[name=submit],:input[id=submit]', form).length) {
			// if there is an input with a name or id of 'submit' then we won't be
			// able to invoke the submit fn on the form (at least not x-browser)
			alert('Error: Form elements must not have name or id of "submit".');
			return;
		}
		
		s = $.extend(true, {}, $.ajaxSettings, options);
		s.context = s.context || s;
		id = 'jqFormIO' + (new Date().getTime());
		if (s.iframeTarget) {
			$io = $(s.iframeTarget);
			n = $io.attr('name');
			if (n == null)
			 	$io.attr('name', id);
			else
				id = n;
		}
		else {
			$io = $('<iframe name="' + id + '" src="'+ s.iframeSrc +'" />');
			$io.css({ position: 'absolute', top: '-1000px', left: '-1000px' });
		}
		io = $io[0];


		xhr = { // mock object
			aborted: 0,
			responseText: null,
			responseXML: null,
			status: 0,
			statusText: 'n/a',
			getAllResponseHeaders: function() {},
			getResponseHeader: function() {},
			setRequestHeader: function() {},
			abort: function(status) {
				var e = (status === 'timeout' ? 'timeout' : 'aborted');
				log('aborting upload... ' + e);
				this.aborted = 1;
				$io.attr('src', s.iframeSrc); // abort op in progress
				xhr.error = e;
				s.error && s.error.call(s.context, xhr, e, status);
				g && $.event.trigger("ajaxError", [xhr, s, e]);
				s.complete && s.complete.call(s.context, xhr, e);
			}
		};

		g = s.global;
		// trigger ajax global events so that activity/block indicators work like normal
		if (g && ! $.active++) {
			$.event.trigger("ajaxStart");
		}
		if (g) {
			$.event.trigger("ajaxSend", [xhr, s]);
		}

		if (s.beforeSend && s.beforeSend.call(s.context, xhr, s) === false) {
			if (s.global) {
				$.active--;
			}
			return;
		}
		if (xhr.aborted) {
			return;
		}

		// add submitting element to data if we know it
		sub = form.clk;
		if (sub) {
			n = sub.name;
			if (n && !sub.disabled) {
				s.extraData = s.extraData || {};
				s.extraData[n] = sub.value;
				if (sub.type == "image") {
					s.extraData[n+'.x'] = form.clk_x;
					s.extraData[n+'.y'] = form.clk_y;
				}
			}
		}
		
		var CLIENT_TIMEOUT_ABORT = 1;
		var SERVER_ABORT = 2;

		function getDoc(frame) {
			var doc = frame.contentWindow ? frame.contentWindow.document : frame.contentDocument ? frame.contentDocument : frame.document;
			return doc;
		}
		
		// take a breath so that pending repaints get some cpu time before the upload starts
		function doSubmit() {
			// make sure form attrs are set
			var t = $form.attr('target'), a = $form.attr('action');

			// update form attrs in IE friendly way
			form.setAttribute('target',id);
			if (!method) {
				form.setAttribute('method', 'POST');
			}
			if (a != s.url) {
				form.setAttribute('action', s.url);
			}

			// ie borks in some cases when setting encoding
			if (! s.skipEncodingOverride && (!method || /post/i.test(method))) {
				$form.attr({
					encoding: 'multipart/form-data',
					enctype:  'multipart/form-data'
				});
			}

			// support timout
			if (s.timeout) {
				timeoutHandle = setTimeout(function() { timedOut = true; cb(CLIENT_TIMEOUT_ABORT); }, s.timeout);
			}
			
			// look for server aborts
			function checkState() {
				try {
					var state = getDoc(io).readyState;
					log('state = ' + state);
					if (state.toLowerCase() == 'uninitialized')
						setTimeout(checkState,50);
				}
				catch(e) {
					log('Server abort: ' , e, ' (', e.name, ')');
					cb(SERVER_ABORT);
					timeoutHandle && clearTimeout(timeoutHandle);
					timeoutHandle = undefined;
				}
			}

			// add "extra" data to form if provided in options
			var extraInputs = [];
			try {
				if (s.extraData) {
					for (var n in s.extraData) {
						extraInputs.push(
							$('<input type="hidden" name="'+n+'" />').attr('value',s.extraData[n])
								.appendTo(form)[0]);
					}
				}

				if (!s.iframeTarget) {
					// add iframe to doc and submit the form
					$io.appendTo('body');
	                io.attachEvent ? io.attachEvent('onload', cb) : io.addEventListener('load', cb, false);
				}
				setTimeout(checkState,15);
				form.submit();
			}
			finally {
				// reset attrs and remove "extra" input elements
				form.setAttribute('action',a);
				if(t) {
					form.setAttribute('target', t);
				} else {
					$form.removeAttr('target');
				}
				$(extraInputs).remove();
			}
		}

		if (s.forceSync) {
			doSubmit();
		}
		else {
			setTimeout(doSubmit, 10); // this lets dom updates render
		}

		var data, doc, domCheckCount = 50, callbackProcessed;

		function cb(e) {
			if (xhr.aborted || callbackProcessed) {
				return;
			}
			try {
				doc = getDoc(io);
			}
			catch(ex) {
				log('cannot access response document: ', ex);
				e = SERVER_ABORT;
			}
			if (e === CLIENT_TIMEOUT_ABORT && xhr) {
				xhr.abort('timeout');
				return;
			}
			else if (e == SERVER_ABORT && xhr) {
				xhr.abort('server abort');
				return;
			}

			if (!doc || doc.location.href == s.iframeSrc) {
				// response not received yet
				if (!timedOut)
					return;
			}
            io.detachEvent ? io.detachEvent('onload', cb) : io.removeEventListener('load', cb, false);

			var status = 'success', errMsg;
			try {
				if (timedOut) {
					throw 'timeout';
				}

				var isXml = s.dataType == 'xml' || doc.XMLDocument || $.isXMLDoc(doc);
				log('isXml='+isXml);
				if (!isXml && window.opera && (doc.body == null || doc.body.innerHTML == '')) {
					if (--domCheckCount) {
						// in some browsers (Opera) the iframe DOM is not always traversable when
						// the onload callback fires, so we loop a bit to accommodate
						log('requeing onLoad callback, DOM not available');
						setTimeout(cb, 250);
						return;
					}
					// let this fall through because server response could be an empty document
					//log('Could not access iframe DOM after mutiple tries.');
					//throw 'DOMException: not available';
				}

				//log('response detected');
                var docRoot = doc.body ? doc.body : doc.documentElement;
                xhr.responseText = docRoot ? docRoot.innerHTML : null;
				xhr.responseXML = doc.XMLDocument ? doc.XMLDocument : doc;
				if (isXml)
					s.dataType = 'xml';
				xhr.getResponseHeader = function(header){
					var headers = {'content-type': s.dataType};
					return headers[header];
				};
                // support for XHR 'status' & 'statusText' emulation :
                if (docRoot) {
                    xhr.status = Number( docRoot.getAttribute('status') ) || xhr.status;
                    xhr.statusText = docRoot.getAttribute('statusText') || xhr.statusText;
                }

				var dt = (s.dataType || '').toLowerCase();
				var scr = /(json|script|text)/.test(dt);
				if (scr || s.textarea) {
					// see if user embedded response in textarea
					var ta = doc.getElementsByTagName('textarea')[0];
					if (ta) {
						xhr.responseText = ta.value;
                        // support for XHR 'status' & 'statusText' emulation :
                        xhr.status = Number( ta.getAttribute('status') ) || xhr.status;
                        xhr.statusText = ta.getAttribute('statusText') || xhr.statusText;
					}
					else if (scr) {
						// account for browsers injecting pre around json response
						var pre = doc.getElementsByTagName('pre')[0];
						var b = doc.getElementsByTagName('body')[0];
						if (pre) {
							xhr.responseText = pre.textContent ? pre.textContent : pre.innerText;
						}
						else if (b) {
							xhr.responseText = b.textContent ? b.textContent : b.innerText;
						}
					}
				}
				else if (dt == 'xml' && !xhr.responseXML && xhr.responseText != null) {
					xhr.responseXML = toXml(xhr.responseText);
				}

                try {
                    data = httpData(xhr, dt, s);
                }
                catch (e) {
                    status = 'parsererror';
                    xhr.error = errMsg = (e || status);
                }
			}
			catch (e) {
				log('error caught: ',e);
				status = 'error';
                xhr.error = errMsg = (e || status);
			}

			if (xhr.aborted) {
				log('upload aborted');
				status = null;
			}

            if (xhr.status) { // we've set xhr.status
                status = (xhr.status >= 200 && xhr.status < 300 || xhr.status === 304) ? 'success' : 'error';
            }

			// ordering of these callbacks/triggers is odd, but that's how $.ajax does it
			if (status === 'success') {
				s.success && s.success.call(s.context, data, 'success', xhr);
				g && $.event.trigger("ajaxSuccess", [xhr, s]);
			}
            else if (status) {
				if (errMsg == undefined)
					errMsg = xhr.statusText;
				s.error && s.error.call(s.context, xhr, status, errMsg);
				g && $.event.trigger("ajaxError", [xhr, s, errMsg]);
            }

			g && $.event.trigger("ajaxComplete", [xhr, s]);

			if (g && ! --$.active) {
				$.event.trigger("ajaxStop");
			}

			s.complete && s.complete.call(s.context, xhr, status);

			callbackProcessed = true;
			if (s.timeout)
				clearTimeout(timeoutHandle);

			// clean up
			setTimeout(function() {
				if (!s.iframeTarget)
					$io.remove();
				xhr.responseXML = null;
			}, 100);
		}

		var toXml = $.parseXML || function(s, doc) { // use parseXML if available (jQuery 1.5+)
			if (window.ActiveXObject) {
				doc = new ActiveXObject('Microsoft.XMLDOM');
				doc.async = 'false';
				doc.loadXML(s);
			}
			else {
				doc = (new DOMParser()).parseFromString(s, 'text/xml');
			}
			return (doc && doc.documentElement && doc.documentElement.nodeName != 'parsererror') ? doc : null;
		};
		var parseJSON = $.parseJSON || function(s) {
			return window['eval']('(' + s + ')');
		};

		var httpData = function( xhr, type, s ) { // mostly lifted from jq1.4.4

			var ct = xhr.getResponseHeader('content-type') || '',
				xml = type === 'xml' || !type && ct.indexOf('xml') >= 0,
				data = xml ? xhr.responseXML : xhr.responseText;

			if (xml && data.documentElement.nodeName === 'parsererror') {
				$.error && $.error('parsererror');
			}
			if (s && s.dataFilter) {
				data = s.dataFilter(data, type);
			}
			if (typeof data === 'string') {
				if (type === 'json' || !type && ct.indexOf('json') >= 0) {
					data = parseJSON(data);
				} else if (type === "script" || !type && ct.indexOf("javascript") >= 0) {
					$.globalEval(data);
				}
			}
			return data;
		};
	}
};

/**
 * ajaxForm() provides a mechanism for fully automating form submission.
 *
 * The advantages of using this method instead of ajaxSubmit() are:
 *
 * 1: This method will include coordinates for <input type="image" /> elements (if the element
 *	is used to submit the form).
 * 2. This method will include the submit element's name/value data (for the element that was
 *	used to submit the form).
 * 3. This method binds the submit() method to the form for you.
 *
 * The options argument for ajaxForm works exactly as it does for ajaxSubmit.  ajaxForm merely
 * passes the options argument along after properly binding events for submit elements and
 * the form itself.
 */
$.fn.ajaxForm = function(options) {
	// in jQuery 1.3+ we can fix mistakes with the ready state
	if (this.length === 0) {
		var o = { s: this.selector, c: this.context };
		if (!$.isReady && o.s) {
			log('DOM not ready, queuing ajaxForm');
			$(function() {
				$(o.s,o.c).ajaxForm(options);
			});
			return this;
		}
		// is your DOM ready?  http://docs.jquery.com/Tutorials:Introducing_$(document).ready()
		log('terminating; zero elements found by selector' + ($.isReady ? '' : ' (DOM not ready)'));
		return this;
	}

	return this.ajaxFormUnbind().bind('submit.form-plugin', function(e) {
		if (!e.isDefaultPrevented()) { // if event has been canceled, don't proceed
			e.preventDefault();
			$(this).ajaxSubmit(options);
		}
	}).bind('click.form-plugin', function(e) {
		var target = e.target;
		var $el = $(target);
		if (!($el.is(":submit,input:image"))) {
			// is this a child element of the submit el?  (ex: a span within a button)
			var t = $el.closest(':submit');
			if (t.length == 0) {
				return;
			}
			target = t[0];
		}
		var form = this;
		form.clk = target;
		if (target.type == 'image') {
			if (e.offsetX != undefined) {
				form.clk_x = e.offsetX;
				form.clk_y = e.offsetY;
			} else if (typeof $.fn.offset == 'function') { // try to use dimensions plugin
				var offset = $el.offset();
				form.clk_x = e.pageX - offset.left;
				form.clk_y = e.pageY - offset.top;
			} else {
				form.clk_x = e.pageX - target.offsetLeft;
				form.clk_y = e.pageY - target.offsetTop;
			}
		}
		// clear form vars
		setTimeout(function() { form.clk = form.clk_x = form.clk_y = null; }, 100);
	});
};

// ajaxFormUnbind unbinds the event handlers that were bound by ajaxForm
$.fn.ajaxFormUnbind = function() {
	return this.unbind('submit.form-plugin click.form-plugin');
};

/**
 * formToArray() gathers form element data into an array of objects that can
 * be passed to any of the following ajax functions: $.get, $.post, or load.
 * Each object in the array has both a 'name' and 'value' property.  An example of
 * an array for a simple login form might be:
 *
 * [ { name: 'username', value: 'jresig' }, { name: 'password', value: 'secret' } ]
 *
 * It is this array that is passed to pre-submit callback functions provided to the
 * ajaxSubmit() and ajaxForm() methods.
 */
$.fn.formToArray = function(semantic) {
	var a = [];
	if (this.length === 0) {
		return a;
	}

	var form = this[0];
	var els = semantic ? form.getElementsByTagName('*') : form.elements;
	if (!els) {
		return a;
	}

	var i,j,n,v,el,max,jmax;
	for(i=0, max=els.length; i < max; i++) {
		el = els[i];
		n = el.name;
		if (!n) {
			continue;
		}

		if (semantic && form.clk && el.type == "image") {
			// handle image inputs on the fly when semantic == true
			if(!el.disabled && form.clk == el) {
				a.push({name: n, value: $(el).val()});
				a.push({name: n+'.x', value: form.clk_x}, {name: n+'.y', value: form.clk_y});
			}
			continue;
		}

		v = $.fieldValue(el, true);
		if (v && v.constructor == Array) {
			for(j=0, jmax=v.length; j < jmax; j++) {
				a.push({name: n, value: v[j]});
			}
		}
		else if (v !== null && typeof v != 'undefined') {
			a.push({name: n, value: v});
		}
	}

	if (!semantic && form.clk) {
		// input type=='image' are not found in elements array! handle it here
		var $input = $(form.clk), input = $input[0];
		n = input.name;
		if (n && !input.disabled && input.type == 'image') {
			a.push({name: n, value: $input.val()});
			a.push({name: n+'.x', value: form.clk_x}, {name: n+'.y', value: form.clk_y});
		}
	}
	return a;
};

/**
 * Serializes form data into a 'submittable' string. This method will return a string
 * in the format: name1=value1&amp;name2=value2
 */
$.fn.formSerialize = function(semantic) {
	//hand off to jQuery.param for proper encoding
	return $.param(this.formToArray(semantic));
};

/**
 * Serializes all field elements in the jQuery object into a query string.
 * This method will return a string in the format: name1=value1&amp;name2=value2
 */
$.fn.fieldSerialize = function(successful) {
	var a = [];
	this.each(function() {
		var n = this.name;
		if (!n) {
			return;
		}
		var v = $.fieldValue(this, successful);
		if (v && v.constructor == Array) {
			for (var i=0,max=v.length; i < max; i++) {
				a.push({name: n, value: v[i]});
			}
		}
		else if (v !== null && typeof v != 'undefined') {
			a.push({name: this.name, value: v});
		}
	});
	//hand off to jQuery.param for proper encoding
	return $.param(a);
};

/**
 * Returns the value(s) of the element in the matched set.  For example, consider the following form:
 *
 *  <form><fieldset>
 *	  <input name="A" type="text" />
 *	  <input name="A" type="text" />
 *	  <input name="B" type="checkbox" value="B1" />
 *	  <input name="B" type="checkbox" value="B2"/>
 *	  <input name="C" type="radio" value="C1" />
 *	  <input name="C" type="radio" value="C2" />
 *  </fieldset></form>
 *
 *  var v = $(':text').fieldValue();
 *  // if no values are entered into the text inputs
 *  v == ['','']
 *  // if values entered into the text inputs are 'foo' and 'bar'
 *  v == ['foo','bar']
 *
 *  var v = $(':checkbox').fieldValue();
 *  // if neither checkbox is checked
 *  v === undefined
 *  // if both checkboxes are checked
 *  v == ['B1', 'B2']
 *
 *  var v = $(':radio').fieldValue();
 *  // if neither radio is checked
 *  v === undefined
 *  // if first radio is checked
 *  v == ['C1']
 *
 * The successful argument controls whether or not the field element must be 'successful'
 * (per http://www.w3.org/TR/html4/interact/forms.html#successful-controls).
 * The default value of the successful argument is true.  If this value is false the value(s)
 * for each element is returned.
 *
 * Note: This method *always* returns an array.  If no valid value can be determined the
 *	   array will be empty, otherwise it will contain one or more values.
 */
$.fn.fieldValue = function(successful) {
	for (var val=[], i=0, max=this.length; i < max; i++) {
		var el = this[i];
		var v = $.fieldValue(el, successful);
		if (v === null || typeof v == 'undefined' || (v.constructor == Array && !v.length)) {
			continue;
		}
		v.constructor == Array ? $.merge(val, v) : val.push(v);
	}
	return val;
};

/**
 * Returns the value of the field element.
 */
$.fieldValue = function(el, successful) {
	var n = el.name, t = el.type, tag = el.tagName.toLowerCase();
	if (successful === undefined) {
		successful = true;
	}

	if (successful && (!n || el.disabled || t == 'reset' || t == 'button' ||
		(t == 'checkbox' || t == 'radio') && !el.checked ||
		(t == 'submit' || t == 'image') && el.form && el.form.clk != el ||
		tag == 'select' && el.selectedIndex == -1)) {
			return null;
	}

	if (tag == 'select') {
		var index = el.selectedIndex;
		if (index < 0) {
			return null;
		}
		var a = [], ops = el.options;
		var one = (t == 'select-one');
		var max = (one ? index+1 : ops.length);
		for(var i=(one ? index : 0); i < max; i++) {
			var op = ops[i];
			if (op.selected) {
				var v = op.value;
				if (!v) { // extra pain for IE...
					v = (op.attributes && op.attributes['value'] && !(op.attributes['value'].specified)) ? op.text : op.value;
				}
				if (one) {
					return v;
				}
				a.push(v);
			}
		}
		return a;
	}
	return $(el).val();
};

/**
 * Clears the form data.  Takes the following actions on the form's input fields:
 *  - input text fields will have their 'value' property set to the empty string
 *  - select elements will have their 'selectedIndex' property set to -1
 *  - checkbox and radio inputs will have their 'checked' property set to false
 *  - inputs of type submit, button, reset, and hidden will *not* be effected
 *  - button elements will *not* be effected
 */
$.fn.clearForm = function(includeHidden) {
	return this.each(function() {
		$('input,select,textarea', this).clearFields(includeHidden);
	});
};

/**
 * Clears the selected form elements.
 */
$.fn.clearFields = $.fn.clearInputs = function(includeHidden) {
	var re = /^(?:color|date|datetime|email|month|number|password|range|search|tel|text|time|url|week)$/i; // 'hidden' is not in this list
	return this.each(function() {
		var t = this.type, tag = this.tagName.toLowerCase();
		if (re.test(t) || tag == 'textarea' || (includeHidden && /hidden/.test(t)) ) {
			this.value = '';
		}
		else if (t == 'checkbox' || t == 'radio') {
			this.checked = false;
		}
		else if (tag == 'select') {
			this.selectedIndex = -1;
		}
	});
};

/**
 * Resets the form data.  Causes all form elements to be reset to their original value.
 */
$.fn.resetForm = function() {
	return this.each(function() {
		// guard against an input with the name of 'reset'
		// note that IE reports the reset function as an 'object'
		if (typeof this.reset == 'function' || (typeof this.reset == 'object' && !this.reset.nodeType)) {
			this.reset();
		}
	});
};

/**
 * Enables or disables any matching elements.
 */
$.fn.enable = function(b) {
	if (b === undefined) {
		b = true;
	}
	return this.each(function() {
		this.disabled = !b;
	});
};

/**
 * Checks/unchecks any matching checkboxes or radio buttons and
 * selects/deselects and matching option elements.
 */
$.fn.selected = function(select) {
	if (select === undefined) {
		select = true;
	}
	return this.each(function() {
		var t = this.type;
		if (t == 'checkbox' || t == 'radio') {
			this.checked = select;
		}
		else if (this.tagName.toLowerCase() == 'option') {
			var $sel = $(this).parent('select');
			if (select && $sel[0] && $sel[0].type == 'select-one') {
				// deselect all other options
				$sel.find('option').selected(false);
			}
			this.selected = select;
		}
	});
};

// expose debug var
$.fn.ajaxSubmit.debug = false;

// helper fn for console logging
function log() {
	if (!$.fn.ajaxSubmit.debug) 
		return;
	var msg = '[jquery.form] ' + Array.prototype.join.call(arguments,'');
	if (window.console && window.console.log) {
		window.console.log(msg);
	}
	else if (window.opera && window.opera.postError) {
		window.opera.postError(msg);
	}
};

})(jQuery);
/*
 * jQuery JSONP Core Plugin 2.3.0 (2012-03-27)
 *
 * http://code.google.com/p/jquery-jsonp/
 *
 * Copyright (c) 2012 Julian Aubourg
 *
 * This document is licensed as free software under the terms of the
 * MIT License: http://www.opensource.org/licenses/mit-license.php
 */
( function( $ ) {

	// ###################### UTILITIES ##

	// Noop
	function noop() {
	}

	// Generic callback
	function genericCallback( data ) {
		lastValue = [ data ];
	}

	// Call if defined
	function callIfDefined( method , object , parameters , returnFlag ) {
		try {
			returnFlag = method && method.apply( object.context || object , parameters );
		} catch( _ ) {
			returnFlag = !1;
		}
		return returnFlag;
	}

	// Give joining character given url
	function qMarkOrAmp( url ) {
		return /\?/ .test( url ) ? "&" : "?";
	}

	var // String constants (for better minification)
		STR_ASYNC = "async",
		STR_CHARSET = "charset",
		STR_EMPTY = "",
		STR_ERROR = "error",
		STR_INSERT_BEFORE = "insertBefore",
		STR_JQUERY_JSONP = "_jqjsp",
		STR_ON = "on",
		STR_ON_CLICK = STR_ON + "click",
		STR_ON_ERROR = STR_ON + STR_ERROR,
		STR_ON_LOAD = STR_ON + "load",
		STR_ON_READY_STATE_CHANGE = STR_ON + "readystatechange",
		STR_READY_STATE = "readyState",
		STR_REMOVE_CHILD = "removeChild",
		STR_SCRIPT_TAG = "<script>",
		STR_SUCCESS = "success",
		STR_TIMEOUT = "timeout",

		// Window
		win = window,
		// Deferred
		Deferred = $.Deferred,
		// Head element
		head = $( "head" )[ 0 ] || document.documentElement,
		// First child
		firstChild = head.firstChild,
		// Page cache
		pageCache = {},
		// Counter
		count = 0,
		// Last returned value
		lastValue,

		// ###################### DEFAULT OPTIONS ##
		xOptionsDefaults = {
			//beforeSend: undefined,
			//cache: false,
			callback: STR_JQUERY_JSONP,
			//callbackParameter: undefined,
			//charset: undefined,
			//complete: undefined,
			//context: undefined,
			//data: "",
			//dataFilter: undefined,
			//error: undefined,
			//pageCache: false,
			//success: undefined,
			//timeout: 0,
			//traditional: false,
			url: location.href
		},

		// opera demands sniffing :/
		opera = win.opera;

	// ###################### MAIN FUNCTION ##
	function jsonp( xOptions ) {

		// Build data with default
		xOptions = $.extend( {} , xOptionsDefaults , xOptions );

		// References to xOptions members (for better minification)
		var successCallback = xOptions.success,
			errorCallback = xOptions.error,
			completeCallback = xOptions.complete,
			dataFilter = xOptions.dataFilter,
			callbackParameter = xOptions.callbackParameter,
			successCallbackName = xOptions.callback,
			cacheFlag = xOptions.cache,
			pageCacheFlag = xOptions.pageCache,
			charset = xOptions.charset,
			url = xOptions.url,
			data = xOptions.data,
			timeout = xOptions.timeout,
			pageCached,

			// Abort/done flag
			done = 0,

			// Life-cycle functions
			cleanUp = noop,

			// Support vars
			supportOnload,
			supportOnreadystatechange,

			// Request execution vars
			script,
			scriptAfter,
			timeoutTimer;

		// If we have Deferreds:
		// - substitute callbacks
		// - promote xOptions to a promise
		Deferred && Deferred(function( defer ) {
			defer.done( successCallback ).fail( errorCallback );
			successCallback = defer.resolve;
			errorCallback = defer.reject;
		}).promise( xOptions );

		// Create the abort method
		xOptions.abort = function() {
			!( done++ ) && cleanUp();
		};

		// Call beforeSend if provided (early abort if false returned)
		if ( callIfDefined( xOptions.beforeSend, xOptions , [ xOptions ] ) === !1 || done ) {
			return xOptions;
		}

		// Control entries
		url = url || STR_EMPTY;
		data = data ? ( (typeof data) == "string" ? data : $.param( data , xOptions.traditional ) ) : STR_EMPTY;

		// Build final url
		url += data ? ( qMarkOrAmp( url ) + data ) : STR_EMPTY;

		// Add callback parameter if provided as option
		callbackParameter && ( url += qMarkOrAmp( url ) + encodeURIComponent( callbackParameter ) + "=?" );

		// Add anticache parameter if needed
		!cacheFlag && !pageCacheFlag && ( url += qMarkOrAmp( url ) + "_" + ( new Date() ).getTime() + "=" );

		// Replace last ? by callback parameter
		url = url.replace( /=\?(&|$)/ , "=" + successCallbackName + "$1" );

		// Success notifier
		function notifySuccess( json ) {

			if ( !( done++ ) ) {

				cleanUp();
				// Pagecache if needed
				pageCacheFlag && ( pageCache [ url ] = { s: [ json ] } );
				// Apply the data filter if provided
				dataFilter && ( json = dataFilter.apply( xOptions , [ json ] ) );
				// Call success then complete
				callIfDefined( successCallback , xOptions , [ json , STR_SUCCESS ] );
				callIfDefined( completeCallback , xOptions , [ xOptions , STR_SUCCESS ] );

			}
		}

		// Error notifier
		function notifyError( type ) {

			if ( !( done++ ) ) {

				// Clean up
				cleanUp();
				// If pure error (not timeout), cache if needed
				pageCacheFlag && type != STR_TIMEOUT && ( pageCache[ url ] = type );
				// Call error then complete
				callIfDefined( errorCallback , xOptions , [ xOptions , type ] );
				callIfDefined( completeCallback , xOptions , [ xOptions , type ] );

			}
		}

		// Check page cache
		if ( pageCacheFlag && ( pageCached = pageCache[ url ] ) ) {

			pageCached.s ? notifySuccess( pageCached.s[ 0 ] ) : notifyError( pageCached );

		} else {

			// Install the generic callback
			// (BEWARE: global namespace pollution ahoy)
			win[ successCallbackName ] = genericCallback;

			// Create the script tag
			script = $( STR_SCRIPT_TAG )[ 0 ];
			script.id = STR_JQUERY_JSONP + count++;

			// Set charset if provided
			if ( charset ) {
				script[ STR_CHARSET ] = charset;
			}

			opera && opera.version() < 11.60 ?
				// onerror is not supported: do not set as async and assume in-order execution.
				// Add a trailing script to emulate the event
				( ( scriptAfter = $( STR_SCRIPT_TAG )[ 0 ] ).text = "document.getElementById('" + script.id + "')." + STR_ON_ERROR + "()" )
			:
				// onerror is supported: set the script as async to avoid requests blocking each others
				( script[ STR_ASYNC ] = STR_ASYNC )

			;

			// Internet Explorer: event/htmlFor trick
			if ( STR_ON_READY_STATE_CHANGE in script ) {

				script.htmlFor = script.id;
				script.event = STR_ON_CLICK;
			}

			// Attached event handlers
			script[ STR_ON_LOAD ] = script[ STR_ON_ERROR ] = script[ STR_ON_READY_STATE_CHANGE ] = function ( result ) {

				// Test readyState if it exists
				if ( !script[ STR_READY_STATE ] || !/i/.test( script[ STR_READY_STATE ] ) ) {

					try {

						script[ STR_ON_CLICK ] && script[ STR_ON_CLICK ]();

					} catch( _ ) {}

					result = lastValue;
					lastValue = 0;
					result ? notifySuccess( result[ 0 ] ) : notifyError( STR_ERROR );

				}
			};

			// Set source
			script.src = url;

			// Re-declare cleanUp function
			cleanUp = function( i ) {
				timeoutTimer && clearTimeout( timeoutTimer );
				script[ STR_ON_READY_STATE_CHANGE ] = script[ STR_ON_LOAD ] = script[ STR_ON_ERROR ]	= null;
				head[ STR_REMOVE_CHILD ]( script );
				scriptAfter && head[ STR_REMOVE_CHILD ]( scriptAfter );
			};

			// Append main script
			head[ STR_INSERT_BEFORE ]( script , firstChild );

			// Append trailing script if needed
			scriptAfter && head[ STR_INSERT_BEFORE ]( scriptAfter , firstChild );

			// If a timeout is needed, install it
			timeoutTimer = timeout > 0 && setTimeout( function() {
				notifyError( STR_TIMEOUT );
			} , timeout );

		}

		return xOptions;
	}

	// ###################### SETUP FUNCTION ##
	jsonp.setup = function( xOptions ) {
		$.extend( xOptionsDefaults , xOptions );
	};

	// ###################### INSTALL in jQuery ##
	$.jsonp = jsonp;

} )( jQuery );

/*!
 * HTML5 Placeholder jQuery Plugin v1.8.2
 * @link http://github.com/mathiasbynens/Placeholder-jQuery-Plugin
 * @author Mathias Bynens <http://mathiasbynens.be/>
 */
(function(f){var e='placeholder' in document.createElement('input'),a='placeholder' in document.createElement('textarea');if(e&&a){f.fn.placeholder=function(){return this};f.fn.placeholder.input=f.fn.placeholder.textarea=true}else{f.fn.placeholder=function(){return this.filter((e?'textarea':':input')+'[placeholder]').bind('focus.placeholder',b).bind('blur.placeholder',d).trigger('blur.placeholder').end()};f.fn.placeholder.input=e;f.fn.placeholder.textarea=a}function c(h){var g={},i=/^jQuery\d+$/;f.each(h.attributes,function(k,j){if(j.specified&&!i.test(j.name)){g[j.name]=j.value}});return g}function b(){var g=f(this);if(g.val()===g.attr('placeholder')&&g.hasClass('placeholder')){if(g.data('placeholder-password')){g.hide().next().attr('id',g.removeAttr('id').data('placeholder-id')).show().focus()}else{g.val('').removeClass('placeholder')}}}function d(h){var l,k=f(this),g=k,j=this.id;if(k.val()===''){if(k.is(':password')){if(!k.data('placeholder-textinput')){try{l=k.clone().attr({type:'text'})}catch(i){l=f('<input>').attr(f.extend(c(this),{type:'text'}))}l.removeAttr('name').data('placeholder-password',true).data('placeholder-id',j).bind('focus.placeholder',b);k.data('placeholder-textinput',l).data('placeholder-id',j).before(l)}k=k.removeAttr('id').hide().prev().attr('id',j).show()}k.addClass('placeholder').val(k.attr('placeholder'))}else{k.removeClass('placeholder')}}f(function(){f('form').bind('submit.placeholder',function(){var g=f('.placeholder',this).each(b);setTimeout(function(){g.each(d)},10)})});f(window).bind('unload.placeholder',function(){f('.placeholder').val('')})}(jQuery));

/*
 * jquery.qtip. The jQuery tooltip plugin
 *
 * Copyright (c) 2009 Craig Thompson
 * http://craigsworks.com
 *
 * Licensed under MIT
 * http://www.opensource.org/licenses/mit-license.php
 *
 * Launch  : February 2009
 * Version : 1.0.0-rc3
 * Released: Tuesday 12th May, 2009 - 00:00
 * Debug: jquery.qtip.debug.js
 */
(function(f){f.fn.qtip=function(B,u){var y,t,A,s,x,w,v,z;if(typeof B=="string"){if(typeof f(this).data("qtip")!=="object"){f.fn.qtip.log.error.call(self,1,f.fn.qtip.constants.NO_TOOLTIP_PRESENT,false)}if(B=="api"){return f(this).data("qtip").interfaces[f(this).data("qtip").current]}else{if(B=="interfaces"){return f(this).data("qtip").interfaces}}}else{if(!B){B={}}if(typeof B.content!=="object"||(B.content.jquery&&B.content.length>0)){B.content={text:B.content}}if(typeof B.content.title!=="object"){B.content.title={text:B.content.title}}if(typeof B.position!=="object"){B.position={corner:B.position}}if(typeof B.position.corner!=="object"){B.position.corner={target:B.position.corner,tooltip:B.position.corner}}if(typeof B.show!=="object"){B.show={when:B.show}}if(typeof B.show.when!=="object"){B.show.when={event:B.show.when}}if(typeof B.show.effect!=="object"){B.show.effect={type:B.show.effect}}if(typeof B.hide!=="object"){B.hide={when:B.hide}}if(typeof B.hide.when!=="object"){B.hide.when={event:B.hide.when}}if(typeof B.hide.effect!=="object"){B.hide.effect={type:B.hide.effect}}if(typeof B.style!=="object"){B.style={name:B.style}}B.style=c(B.style);s=f.extend(true,{},f.fn.qtip.defaults,B);s.style=a.call({options:s},s.style);s.user=f.extend(true,{},B)}return f(this).each(function(){if(typeof B=="string"){w=B.toLowerCase();A=f(this).qtip("interfaces");if(typeof A=="object"){if(u===true&&w=="destroy"){while(A.length>0){A[A.length-1].destroy()}}else{if(u!==true){A=[f(this).qtip("api")]}for(y=0;y<A.length;y++){if(w=="destroy"){A[y].destroy()}else{if(A[y].status.rendered===true){if(w=="show"){A[y].show()}else{if(w=="hide"){A[y].hide()}else{if(w=="focus"){A[y].focus()}else{if(w=="disable"){A[y].disable(true)}else{if(w=="enable"){A[y].disable(false)}}}}}}}}}}}else{v=f.extend(true,{},s);v.hide.effect.length=s.hide.effect.length;v.show.effect.length=s.show.effect.length;if(v.position.container===false){v.position.container=f(document.body)}if(v.position.target===false){v.position.target=f(this)}if(v.show.when.target===false){v.show.when.target=f(this)}if(v.hide.when.target===false){v.hide.when.target=f(this)}t=f.fn.qtip.interfaces.length;for(y=0;y<t;y++){if(typeof f.fn.qtip.interfaces[y]=="undefined"){t=y;break}}x=new d(f(this),v,t);f.fn.qtip.interfaces[t]=x;if(typeof f(this).data("qtip")=="object"){if(typeof f(this).attr("qtip")==="undefined"){f(this).data("qtip").current=f(this).data("qtip").interfaces.length}f(this).data("qtip").interfaces.push(x)}else{f(this).data("qtip",{current:0,interfaces:[x]})}if(v.content.prerender===false&&v.show.when.event!==false&&v.show.ready!==true){v.show.when.target.bind(v.show.when.event+".qtip-"+t+"-create",{qtip:t},function(C){z=f.fn.qtip.interfaces[C.data.qtip];z.options.show.when.target.unbind(z.options.show.when.event+".qtip-"+C.data.qtip+"-create");z.cache.mouse={x:C.pageX,y:C.pageY};p.call(z);z.options.show.when.target.trigger(z.options.show.when.event)})}else{x.cache.mouse={x:v.show.when.target.offset().left,y:v.show.when.target.offset().top};p.call(x)}}})};function d(u,t,v){var s=this;s.id=v;s.options=t;s.status={animated:false,rendered:false,disabled:false,focused:false};s.elements={target:u.addClass(s.options.style.classes.target),tooltip:null,wrapper:null,content:null,contentWrapper:null,title:null,button:null,tip:null,bgiframe:null};s.cache={mouse:{},position:{},toggle:0};s.timers={};f.extend(s,s.options.api,{show:function(y){var x,z;if(!s.status.rendered){return f.fn.qtip.log.error.call(s,2,f.fn.qtip.constants.TOOLTIP_NOT_RENDERED,"show")}if(s.elements.tooltip.css("display")!=="none"){return s}s.elements.tooltip.stop(true,false);x=s.beforeShow.call(s,y);if(x===false){return s}function w(){if(s.options.position.type!=="static"){s.focus()}s.onShow.call(s,y);if(f.browser.msie){s.elements.tooltip.get(0).style.removeAttribute("filter")}}s.cache.toggle=1;if(s.options.position.type!=="static"){s.updatePosition(y,(s.options.show.effect.length>0))}if(typeof s.options.show.solo=="object"){z=f(s.options.show.solo)}else{if(s.options.show.solo===true){z=f("div.qtip").not(s.elements.tooltip)}}if(z){z.each(function(){if(f(this).qtip("api").status.rendered===true){f(this).qtip("api").hide()}})}if(typeof s.options.show.effect.type=="function"){s.options.show.effect.type.call(s.elements.tooltip,s.options.show.effect.length);s.elements.tooltip.queue(function(){w();f(this).dequeue()})}else{switch(s.options.show.effect.type.toLowerCase()){case"fade":s.elements.tooltip.fadeIn(s.options.show.effect.length,w);break;case"slide":s.elements.tooltip.slideDown(s.options.show.effect.length,function(){w();if(s.options.position.type!=="static"){s.updatePosition(y,true)}});break;case"grow":s.elements.tooltip.show(s.options.show.effect.length,w);break;default:s.elements.tooltip.show(null,w);break}s.elements.tooltip.addClass(s.options.style.classes.active)}return f.fn.qtip.log.error.call(s,1,f.fn.qtip.constants.EVENT_SHOWN,"show")},hide:function(y){var x;if(!s.status.rendered){return f.fn.qtip.log.error.call(s,2,f.fn.qtip.constants.TOOLTIP_NOT_RENDERED,"hide")}else{if(s.elements.tooltip.css("display")==="none"){return s}}clearTimeout(s.timers.show);s.elements.tooltip.stop(true,false);x=s.beforeHide.call(s,y);if(x===false){return s}function w(){s.onHide.call(s,y)}s.cache.toggle=0;if(typeof s.options.hide.effect.type=="function"){s.options.hide.effect.type.call(s.elements.tooltip,s.options.hide.effect.length);s.elements.tooltip.queue(function(){w();f(this).dequeue()})}else{switch(s.options.hide.effect.type.toLowerCase()){case"fade":s.elements.tooltip.fadeOut(s.options.hide.effect.length,w);break;case"slide":s.elements.tooltip.slideUp(s.options.hide.effect.length,w);break;case"grow":s.elements.tooltip.hide(s.options.hide.effect.length,w);break;default:s.elements.tooltip.hide(null,w);break}s.elements.tooltip.removeClass(s.options.style.classes.active)}return f.fn.qtip.log.error.call(s,1,f.fn.qtip.constants.EVENT_HIDDEN,"hide")},updatePosition:function(w,x){var C,G,L,J,H,E,y,I,B,D,K,A,F,z;if(!s.status.rendered){return f.fn.qtip.log.error.call(s,2,f.fn.qtip.constants.TOOLTIP_NOT_RENDERED,"updatePosition")}else{if(s.options.position.type=="static"){return f.fn.qtip.log.error.call(s,1,f.fn.qtip.constants.CANNOT_POSITION_STATIC,"updatePosition")}}G={position:{left:0,top:0},dimensions:{height:0,width:0},corner:s.options.position.corner.target};L={position:s.getPosition(),dimensions:s.getDimensions(),corner:s.options.position.corner.tooltip};if(s.options.position.target!=="mouse"){if(s.options.position.target.get(0).nodeName.toLowerCase()=="area"){J=s.options.position.target.attr("coords").split(",");for(C=0;C<J.length;C++){J[C]=parseInt(J[C])}H=s.options.position.target.parent("map").attr("name");E=f('img[usemap="#'+H+'"]:first').offset();G.position={left:Math.floor(E.left+J[0]),top:Math.floor(E.top+J[1])};switch(s.options.position.target.attr("shape").toLowerCase()){case"rect":G.dimensions={width:Math.ceil(Math.abs(J[2]-J[0])),height:Math.ceil(Math.abs(J[3]-J[1]))};break;case"circle":G.dimensions={width:J[2]+1,height:J[2]+1};break;case"poly":G.dimensions={width:J[0],height:J[1]};for(C=0;C<J.length;C++){if(C%2==0){if(J[C]>G.dimensions.width){G.dimensions.width=J[C]}if(J[C]<J[0]){G.position.left=Math.floor(E.left+J[C])}}else{if(J[C]>G.dimensions.height){G.dimensions.height=J[C]}if(J[C]<J[1]){G.position.top=Math.floor(E.top+J[C])}}}G.dimensions.width=G.dimensions.width-(G.position.left-E.left);G.dimensions.height=G.dimensions.height-(G.position.top-E.top);break;default:return f.fn.qtip.log.error.call(s,4,f.fn.qtip.constants.INVALID_AREA_SHAPE,"updatePosition");break}G.dimensions.width-=2;G.dimensions.height-=2}else{if(s.options.position.target.add(document.body).length===1){G.position={left:f(document).scrollLeft(),top:f(document).scrollTop()};G.dimensions={height:f(window).height(),width:f(window).width()}}else{if(typeof s.options.position.target.attr("qtip")!=="undefined"){G.position=s.options.position.target.qtip("api").cache.position}else{G.position=s.options.position.target.offset()}G.dimensions={height:s.options.position.target.outerHeight(),width:s.options.position.target.outerWidth()}}}y=f.extend({},G.position);if(G.corner.search(/right/i)!==-1){y.left+=G.dimensions.width}if(G.corner.search(/bottom/i)!==-1){y.top+=G.dimensions.height}if(G.corner.search(/((top|bottom)Middle)|center/)!==-1){y.left+=(G.dimensions.width/2)}if(G.corner.search(/((left|right)Middle)|center/)!==-1){y.top+=(G.dimensions.height/2)}}else{G.position=y={left:s.cache.mouse.x,top:s.cache.mouse.y};G.dimensions={height:1,width:1}}if(L.corner.search(/right/i)!==-1){y.left-=L.dimensions.width}if(L.corner.search(/bottom/i)!==-1){y.top-=L.dimensions.height}if(L.corner.search(/((top|bottom)Middle)|center/)!==-1){y.left-=(L.dimensions.width/2)}if(L.corner.search(/((left|right)Middle)|center/)!==-1){y.top-=(L.dimensions.height/2)}I=(f.browser.msie)?1:0;B=(f.browser.msie&&parseInt(f.browser.version.charAt(0))===6)?1:0;if(s.options.style.border.radius>0){if(L.corner.search(/Left/)!==-1){y.left-=s.options.style.border.radius}else{if(L.corner.search(/Right/)!==-1){y.left+=s.options.style.border.radius}}if(L.corner.search(/Top/)!==-1){y.top-=s.options.style.border.radius}else{if(L.corner.search(/Bottom/)!==-1){y.top+=s.options.style.border.radius}}}if(I){if(L.corner.search(/top/)!==-1){y.top-=I}else{if(L.corner.search(/bottom/)!==-1){y.top+=I}}if(L.corner.search(/left/)!==-1){y.left-=I}else{if(L.corner.search(/right/)!==-1){y.left+=I}}if(L.corner.search(/leftMiddle|rightMiddle/)!==-1){y.top-=1}}if(s.options.position.adjust.screen===true){y=o.call(s,y,G,L)}if(s.options.position.target==="mouse"&&s.options.position.adjust.mouse===true){if(s.options.position.adjust.screen===true&&s.elements.tip){K=s.elements.tip.attr("rel")}else{K=s.options.position.corner.tooltip}y.left+=(K.search(/right/i)!==-1)?-6:6;y.top+=(K.search(/bottom/i)!==-1)?-6:6}if(!s.elements.bgiframe&&f.browser.msie&&parseInt(f.browser.version.charAt(0))==6){f("select, object").each(function(){A=f(this).offset();A.bottom=A.top+f(this).height();A.right=A.left+f(this).width();if(y.top+L.dimensions.height>=A.top&&y.left+L.dimensions.width>=A.left){k.call(s)}})}y.left+=s.options.position.adjust.x;y.top+=s.options.position.adjust.y;F=s.getPosition();if(y.left!=F.left||y.top!=F.top){z=s.beforePositionUpdate.call(s,w);if(z===false){return s}s.cache.position=y;if(x===true){s.status.animated=true;s.elements.tooltip.animate(y,200,"swing",function(){s.status.animated=false})}else{s.elements.tooltip.css(y)}s.onPositionUpdate.call(s,w);if(typeof w!=="undefined"&&w.type&&w.type!=="mousemove"){f.fn.qtip.log.error.call(s,1,f.fn.qtip.constants.EVENT_POSITION_UPDATED,"updatePosition")}}return s},updateWidth:function(w){var x;if(!s.status.rendered){return f.fn.qtip.log.error.call(s,2,f.fn.qtip.constants.TOOLTIP_NOT_RENDERED,"updateWidth")}else{if(w&&typeof w!=="number"){return f.fn.qtip.log.error.call(s,2,"newWidth must be of type number","updateWidth")}}x=s.elements.contentWrapper.siblings().add(s.elements.tip).add(s.elements.button);if(!w){if(typeof s.options.style.width.value=="number"){w=s.options.style.width.value}else{s.elements.tooltip.css({width:"auto"});x.hide();if(f.browser.msie){s.elements.wrapper.add(s.elements.contentWrapper.children()).css({zoom:"normal"})}w=s.getDimensions().width+1;if(!s.options.style.width.value){if(w>s.options.style.width.max){w=s.options.style.width.max}if(w<s.options.style.width.min){w=s.options.style.width.min}}}}if(w%2!==0){w-=1}s.elements.tooltip.width(w);x.show();if(s.options.style.border.radius){s.elements.tooltip.find(".qtip-betweenCorners").each(function(y){f(this).width(w-(s.options.style.border.radius*2))})}if(f.browser.msie){s.elements.wrapper.add(s.elements.contentWrapper.children()).css({zoom:"1"});s.elements.wrapper.width(w);if(s.elements.bgiframe){s.elements.bgiframe.width(w).height(s.getDimensions.height)}}return f.fn.qtip.log.error.call(s,1,f.fn.qtip.constants.EVENT_WIDTH_UPDATED,"updateWidth")},updateStyle:function(w){var z,A,x,y,B;if(!s.status.rendered){return f.fn.qtip.log.error.call(s,2,f.fn.qtip.constants.TOOLTIP_NOT_RENDERED,"updateStyle")}else{if(typeof w!=="string"||!f.fn.qtip.styles[w]){return f.fn.qtip.log.error.call(s,2,f.fn.qtip.constants.STYLE_NOT_DEFINED,"updateStyle")}}s.options.style=a.call(s,f.fn.qtip.styles[w],s.options.user.style);s.elements.content.css(q(s.options.style));if(s.options.content.title.text!==false){s.elements.title.css(q(s.options.style.title,true))}s.elements.contentWrapper.css({borderColor:s.options.style.border.color});if(s.options.style.tip.corner!==false){if(f("<canvas>").get(0).getContext){z=s.elements.tooltip.find(".qtip-tip canvas:first");x=z.get(0).getContext("2d");x.clearRect(0,0,300,300);y=z.parent("div[rel]:first").attr("rel");B=b(y,s.options.style.tip.size.width,s.options.style.tip.size.height);h.call(s,z,B,s.options.style.tip.color||s.options.style.border.color)}else{if(f.browser.msie){z=s.elements.tooltip.find('.qtip-tip [nodeName="shape"]');z.attr("fillcolor",s.options.style.tip.color||s.options.style.border.color)}}}if(s.options.style.border.radius>0){s.elements.tooltip.find(".qtip-betweenCorners").css({backgroundColor:s.options.style.border.color});if(f("<canvas>").get(0).getContext){A=g(s.options.style.border.radius);s.elements.tooltip.find(".qtip-wrapper canvas").each(function(){x=f(this).get(0).getContext("2d");x.clearRect(0,0,300,300);y=f(this).parent("div[rel]:first").attr("rel");r.call(s,f(this),A[y],s.options.style.border.radius,s.options.style.border.color)})}else{if(f.browser.msie){s.elements.tooltip.find('.qtip-wrapper [nodeName="arc"]').each(function(){f(this).attr("fillcolor",s.options.style.border.color)})}}}return f.fn.qtip.log.error.call(s,1,f.fn.qtip.constants.EVENT_STYLE_UPDATED,"updateStyle")},updateContent:function(A,y){var z,x,w;if(!s.status.rendered){return f.fn.qtip.log.error.call(s,2,f.fn.qtip.constants.TOOLTIP_NOT_RENDERED,"updateContent")}else{if(!A){return f.fn.qtip.log.error.call(s,2,f.fn.qtip.constants.NO_CONTENT_PROVIDED,"updateContent")}}z=s.beforeContentUpdate.call(s,A);if(typeof z=="string"){A=z}else{if(z===false){return}}if(f.browser.msie){s.elements.contentWrapper.children().css({zoom:"normal"})}if(A.jquery&&A.length>0){A.clone(true).appendTo(s.elements.content).show()}else{s.elements.content.html(A)}x=s.elements.content.find("img[complete=false]");if(x.length>0){w=0;x.each(function(C){f('<img src="'+f(this).attr("src")+'" />').load(function(){if(++w==x.length){B()}})})}else{B()}function B(){s.updateWidth();if(y!==false){if(s.options.position.type!=="static"){s.updatePosition(s.elements.tooltip.is(":visible"),true)}if(s.options.style.tip.corner!==false){n.call(s)}}}s.onContentUpdate.call(s);return f.fn.qtip.log.error.call(s,1,f.fn.qtip.constants.EVENT_CONTENT_UPDATED,"loadContent")},loadContent:function(w,z,A){var y;if(!s.status.rendered){return f.fn.qtip.log.error.call(s,2,f.fn.qtip.constants.TOOLTIP_NOT_RENDERED,"loadContent")}y=s.beforeContentLoad.call(s);if(y===false){return s}if(A=="post"){f.post(w,z,x)}else{f.get(w,z,x)}function x(B){s.onContentLoad.call(s);f.fn.qtip.log.error.call(s,1,f.fn.qtip.constants.EVENT_CONTENT_LOADED,"loadContent");s.updateContent(B)}return s},updateTitle:function(w){if(!s.status.rendered){return f.fn.qtip.log.error.call(s,2,f.fn.qtip.constants.TOOLTIP_NOT_RENDERED,"updateTitle")}else{if(!w){return f.fn.qtip.log.error.call(s,2,f.fn.qtip.constants.NO_CONTENT_PROVIDED,"updateTitle")}}returned=s.beforeTitleUpdate.call(s);if(returned===false){return s}if(s.elements.button){s.elements.button=s.elements.button.clone(true)}s.elements.title.html(w);if(s.elements.button){s.elements.title.prepend(s.elements.button)}s.onTitleUpdate.call(s);return f.fn.qtip.log.error.call(s,1,f.fn.qtip.constants.EVENT_TITLE_UPDATED,"updateTitle")},focus:function(A){var y,x,w,z;if(!s.status.rendered){return f.fn.qtip.log.error.call(s,2,f.fn.qtip.constants.TOOLTIP_NOT_RENDERED,"focus")}else{if(s.options.position.type=="static"){return f.fn.qtip.log.error.call(s,1,f.fn.qtip.constants.CANNOT_FOCUS_STATIC,"focus")}}y=parseInt(s.elements.tooltip.css("z-index"));x=6000+f("div.qtip[qtip]").length-1;if(!s.status.focused&&y!==x){z=s.beforeFocus.call(s,A);if(z===false){return s}f("div.qtip[qtip]").not(s.elements.tooltip).each(function(){if(f(this).qtip("api").status.rendered===true){w=parseInt(f(this).css("z-index"));if(typeof w=="number"&&w>-1){f(this).css({zIndex:parseInt(f(this).css("z-index"))-1})}f(this).qtip("api").status.focused=false}});s.elements.tooltip.css({zIndex:x});s.status.focused=true;s.onFocus.call(s,A);f.fn.qtip.log.error.call(s,1,f.fn.qtip.constants.EVENT_FOCUSED,"focus")}return s},disable:function(w){if(!s.status.rendered){return f.fn.qtip.log.error.call(s,2,f.fn.qtip.constants.TOOLTIP_NOT_RENDERED,"disable")}if(w){if(!s.status.disabled){s.status.disabled=true;f.fn.qtip.log.error.call(s,1,f.fn.qtip.constants.EVENT_DISABLED,"disable")}else{f.fn.qtip.log.error.call(s,1,f.fn.qtip.constants.TOOLTIP_ALREADY_DISABLED,"disable")}}else{if(s.status.disabled){s.status.disabled=false;f.fn.qtip.log.error.call(s,1,f.fn.qtip.constants.EVENT_ENABLED,"disable")}else{f.fn.qtip.log.error.call(s,1,f.fn.qtip.constants.TOOLTIP_ALREADY_ENABLED,"disable")}}return s},destroy:function(){var w,x,y;x=s.beforeDestroy.call(s);if(x===false){return s}if(s.status.rendered){s.options.show.when.target.unbind("mousemove.qtip",s.updatePosition);s.options.show.when.target.unbind("mouseout.qtip",s.hide);s.options.show.when.target.unbind(s.options.show.when.event+".qtip");s.options.hide.when.target.unbind(s.options.hide.when.event+".qtip");s.elements.tooltip.unbind(s.options.hide.when.event+".qtip");s.elements.tooltip.unbind("mouseover.qtip",s.focus);s.elements.tooltip.remove()}else{s.options.show.when.target.unbind(s.options.show.when.event+".qtip-create")}if(typeof s.elements.target.data("qtip")=="object"){y=s.elements.target.data("qtip").interfaces;if(typeof y=="object"&&y.length>0){for(w=0;w<y.length-1;w++){if(y[w].id==s.id){y.splice(w,1)}}}}delete f.fn.qtip.interfaces[s.id];if(typeof y=="object"&&y.length>0){s.elements.target.data("qtip").current=y.length-1}else{s.elements.target.removeData("qtip")}s.onDestroy.call(s);f.fn.qtip.log.error.call(s,1,f.fn.qtip.constants.EVENT_DESTROYED,"destroy");return s.elements.target},getPosition:function(){var w,x;if(!s.status.rendered){return f.fn.qtip.log.error.call(s,2,f.fn.qtip.constants.TOOLTIP_NOT_RENDERED,"getPosition")}w=(s.elements.tooltip.css("display")!=="none")?false:true;if(w){s.elements.tooltip.css({visiblity:"hidden"}).show()}x=s.elements.tooltip.offset();if(w){s.elements.tooltip.css({visiblity:"visible"}).hide()}return x},getDimensions:function(){var w,x;if(!s.status.rendered){return f.fn.qtip.log.error.call(s,2,f.fn.qtip.constants.TOOLTIP_NOT_RENDERED,"getDimensions")}w=(!s.elements.tooltip.is(":visible"))?true:false;if(w){s.elements.tooltip.css({visiblity:"hidden"}).show()}x={height:s.elements.tooltip.outerHeight(),width:s.elements.tooltip.outerWidth()};if(w){s.elements.tooltip.css({visiblity:"visible"}).hide()}return x}})}function p(){var s,w,u,t,v,y,x;s=this;s.beforeRender.call(s);s.status.rendered=true;s.elements.tooltip='<div qtip="'+s.id+'" class="qtip '+(s.options.style.classes.tooltip||s.options.style)+'"style="display:none; -moz-border-radius:0; -webkit-border-radius:0; border-radius:0;position:'+s.options.position.type+';">  <div class="qtip-wrapper" style="position:relative; overflow:hidden; text-align:left;">    <div class="qtip-contentWrapper" style="overflow:hidden;">       <div class="qtip-content '+s.options.style.classes.content+'"></div></div></div></div>';s.elements.tooltip=f(s.elements.tooltip);s.elements.tooltip.appendTo(s.options.position.container);s.elements.tooltip.data("qtip",{current:0,interfaces:[s]});s.elements.wrapper=s.elements.tooltip.children("div:first");s.elements.contentWrapper=s.elements.wrapper.children("div:first").css({background:s.options.style.background});s.elements.content=s.elements.contentWrapper.children("div:first").css(q(s.options.style));if(f.browser.msie){s.elements.wrapper.add(s.elements.content).css({zoom:1})}if(s.options.hide.when.event=="unfocus"){s.elements.tooltip.attr("unfocus",true)}if(typeof s.options.style.width.value=="number"){s.updateWidth()}if(f("<canvas>").get(0).getContext||f.browser.msie){if(s.options.style.border.radius>0){m.call(s)}else{s.elements.contentWrapper.css({border:s.options.style.border.width+"px solid "+s.options.style.border.color})}if(s.options.style.tip.corner!==false){e.call(s)}}else{s.elements.contentWrapper.css({border:s.options.style.border.width+"px solid "+s.options.style.border.color});s.options.style.border.radius=0;s.options.style.tip.corner=false;f.fn.qtip.log.error.call(s,2,f.fn.qtip.constants.CANVAS_VML_NOT_SUPPORTED,"render")}if((typeof s.options.content.text=="string"&&s.options.content.text.length>0)||(s.options.content.text.jquery&&s.options.content.text.length>0)){u=s.options.content.text}else{if(typeof s.elements.target.attr("title")=="string"&&s.elements.target.attr("title").length>0){u=s.elements.target.attr("title").replace("\\n","<br />");s.elements.target.attr("title","")}else{if(typeof s.elements.target.attr("alt")=="string"&&s.elements.target.attr("alt").length>0){u=s.elements.target.attr("alt").replace("\\n","<br />");s.elements.target.attr("alt","")}else{u=" ";f.fn.qtip.log.error.call(s,1,f.fn.qtip.constants.NO_VALID_CONTENT,"render")}}}if(s.options.content.title.text!==false){j.call(s)}s.updateContent(u);l.call(s);if(s.options.show.ready===true){s.show()}if(s.options.content.url!==false){t=s.options.content.url;v=s.options.content.data;y=s.options.content.method||"get";s.loadContent(t,v,y)}s.onRender.call(s);f.fn.qtip.log.error.call(s,1,f.fn.qtip.constants.EVENT_RENDERED,"render")}function m(){var F,z,t,B,x,E,u,G,D,y,w,C,A,s,v;F=this;F.elements.wrapper.find(".qtip-borderBottom, .qtip-borderTop").remove();t=F.options.style.border.width;B=F.options.style.border.radius;x=F.options.style.border.color||F.options.style.tip.color;E=g(B);u={};for(z in E){u[z]='<div rel="'+z+'" style="'+((z.search(/Left/)!==-1)?"left":"right")+":0; position:absolute; height:"+B+"px; width:"+B+'px; overflow:hidden; line-height:0.1px; font-size:1px">';if(f("<canvas>").get(0).getContext){u[z]+='<canvas height="'+B+'" width="'+B+'" style="vertical-align: top"></canvas>'}else{if(f.browser.msie){G=B*2+3;u[z]+='<v:arc stroked="false" fillcolor="'+x+'" startangle="'+E[z][0]+'" endangle="'+E[z][1]+'" style="width:'+G+"px; height:"+G+"px; margin-top:"+((z.search(/bottom/)!==-1)?-2:-1)+"px; margin-left:"+((z.search(/Right/)!==-1)?E[z][2]-3.5:-1)+'px; vertical-align:top; display:inline-block; behavior:url(#default#VML)"></v:arc>'}}u[z]+="</div>"}D=F.getDimensions().width-(Math.max(t,B)*2);y='<div class="qtip-betweenCorners" style="height:'+B+"px; width:"+D+"px; overflow:hidden; background-color:"+x+'; line-height:0.1px; font-size:1px;">';w='<div class="qtip-borderTop" dir="ltr" style="height:'+B+"px; margin-left:"+B+'px; line-height:0.1px; font-size:1px; padding:0;">'+u.topLeft+u.topRight+y;F.elements.wrapper.prepend(w);C='<div class="qtip-borderBottom" dir="ltr" style="height:'+B+"px; margin-left:"+B+'px; line-height:0.1px; font-size:1px; padding:0;">'+u.bottomLeft+u.bottomRight+y;F.elements.wrapper.append(C);if(f("<canvas>").get(0).getContext){F.elements.wrapper.find("canvas").each(function(){A=E[f(this).parent("[rel]:first").attr("rel")];r.call(F,f(this),A,B,x)})}else{if(f.browser.msie){F.elements.tooltip.append('<v:image style="behavior:url(#default#VML);"></v:image>')}}s=Math.max(B,(B+(t-B)));v=Math.max(t-B,0);F.elements.contentWrapper.css({border:"0px solid "+x,borderWidth:v+"px "+s+"px"})}function r(u,w,s,t){var v=u.get(0).getContext("2d");v.fillStyle=t;v.beginPath();v.arc(w[0],w[1],s,0,Math.PI*2,false);v.fill()}function e(v){var t,s,x,u,w;t=this;if(t.elements.tip!==null){t.elements.tip.remove()}s=t.options.style.tip.color||t.options.style.border.color;if(t.options.style.tip.corner===false){return}else{if(!v){v=t.options.style.tip.corner}}x=b(v,t.options.style.tip.size.width,t.options.style.tip.size.height);t.elements.tip='<div class="'+t.options.style.classes.tip+'" dir="ltr" rel="'+v+'" style="position:absolute; height:'+t.options.style.tip.size.height+"px; width:"+t.options.style.tip.size.width+'px; margin:0 auto; line-height:0.1px; font-size:1px;">';if(f("<canvas>").get(0).getContext){t.elements.tip+='<canvas height="'+t.options.style.tip.size.height+'" width="'+t.options.style.tip.size.width+'"></canvas>'}else{if(f.browser.msie){u=t.options.style.tip.size.width+","+t.options.style.tip.size.height;w="m"+x[0][0]+","+x[0][1];w+=" l"+x[1][0]+","+x[1][1];w+=" "+x[2][0]+","+x[2][1];w+=" xe";t.elements.tip+='<v:shape fillcolor="'+s+'" stroked="false" filled="true" path="'+w+'" coordsize="'+u+'" style="width:'+t.options.style.tip.size.width+"px; height:"+t.options.style.tip.size.height+"px; line-height:0.1px; display:inline-block; behavior:url(#default#VML); vertical-align:"+((v.search(/top/)!==-1)?"bottom":"top")+'"></v:shape>';t.elements.tip+='<v:image style="behavior:url(#default#VML);"></v:image>';t.elements.contentWrapper.css("position","relative")}}t.elements.tooltip.prepend(t.elements.tip+"</div>");t.elements.tip=t.elements.tooltip.find("."+t.options.style.classes.tip).eq(0);if(f("<canvas>").get(0).getContext){h.call(t,t.elements.tip.find("canvas:first"),x,s)}if(v.search(/top/)!==-1&&f.browser.msie&&parseInt(f.browser.version.charAt(0))===6){t.elements.tip.css({marginTop:-4})}n.call(t,v)}function h(t,v,s){var u=t.get(0).getContext("2d");u.fillStyle=s;u.beginPath();u.moveTo(v[0][0],v[0][1]);u.lineTo(v[1][0],v[1][1]);u.lineTo(v[2][0],v[2][1]);u.fill()}function n(u){var t,w,s,x,v;t=this;if(t.options.style.tip.corner===false||!t.elements.tip){return}if(!u){u=t.elements.tip.attr("rel")}w=positionAdjust=(f.browser.msie)?1:0;t.elements.tip.css(u.match(/left|right|top|bottom/)[0],0);if(u.search(/top|bottom/)!==-1){if(f.browser.msie){if(parseInt(f.browser.version.charAt(0))===6){positionAdjust=(u.search(/top/)!==-1)?-3:1}else{positionAdjust=(u.search(/top/)!==-1)?1:2}}if(u.search(/Middle/)!==-1){t.elements.tip.css({left:"50%",marginLeft:-(t.options.style.tip.size.width/2)})}else{if(u.search(/Left/)!==-1){t.elements.tip.css({left:t.options.style.border.radius-w})}else{if(u.search(/Right/)!==-1){t.elements.tip.css({right:t.options.style.border.radius+w})}}}if(u.search(/top/)!==-1){t.elements.tip.css({top:-positionAdjust})}else{t.elements.tip.css({bottom:positionAdjust})}}else{if(u.search(/left|right/)!==-1){if(f.browser.msie){positionAdjust=(parseInt(f.browser.version.charAt(0))===6)?1:((u.search(/left/)!==-1)?1:2)}if(u.search(/Middle/)!==-1){t.elements.tip.css({top:"50%",marginTop:-(t.options.style.tip.size.height/2)})}else{if(u.search(/Top/)!==-1){t.elements.tip.css({top:t.options.style.border.radius-w})}else{if(u.search(/Bottom/)!==-1){t.elements.tip.css({bottom:t.options.style.border.radius+w})}}}if(u.search(/left/)!==-1){t.elements.tip.css({left:-positionAdjust})}else{t.elements.tip.css({right:positionAdjust})}}}s="padding-"+u.match(/left|right|top|bottom/)[0];x=t.options.style.tip.size[(s.search(/left|right/)!==-1)?"width":"height"];t.elements.tooltip.css("padding",0);t.elements.tooltip.css(s,x);if(f.browser.msie&&parseInt(f.browser.version.charAt(0))==6){v=parseInt(t.elements.tip.css("margin-top"))||0;v+=parseInt(t.elements.content.css("margin-top"))||0;t.elements.tip.css({marginTop:v})}}function j(){var s=this;if(s.elements.title!==null){s.elements.title.remove()}s.elements.title=f('<div class="'+s.options.style.classes.title+'">').css(q(s.options.style.title,true)).css({zoom:(f.browser.msie)?1:0}).prependTo(s.elements.contentWrapper);if(s.options.content.title.text){s.updateTitle.call(s,s.options.content.title.text)}if(s.options.content.title.button!==false&&typeof s.options.content.title.button=="string"){s.elements.button=f('<a class="'+s.options.style.classes.button+'" style="float:right; position: relative"></a>').css(q(s.options.style.button,true)).html(s.options.content.title.button).prependTo(s.elements.title).click(function(t){if(!s.status.disabled){s.hide(t)}})}}function l(){var t,v,u,s;t=this;v=t.options.show.when.target;u=t.options.hide.when.target;if(t.options.hide.fixed){u=u.add(t.elements.tooltip)}if(t.options.hide.when.event=="inactive"){s=["click","dblclick","mousedown","mouseup","mousemove","mouseout","mouseenter","mouseleave","mouseover"];function y(z){if(t.status.disabled===true){return}clearTimeout(t.timers.inactive);t.timers.inactive=setTimeout(function(){f(s).each(function(){u.unbind(this+".qtip-inactive");t.elements.content.unbind(this+".qtip-inactive")});t.hide(z)},t.options.hide.delay)}}else{if(t.options.hide.fixed===true){t.elements.tooltip.bind("mouseover.qtip",function(){if(t.status.disabled===true){return}clearTimeout(t.timers.hide)})}}function x(z){if(t.status.disabled===true){return}if(t.options.hide.when.event=="inactive"){f(s).each(function(){u.bind(this+".qtip-inactive",y);t.elements.content.bind(this+".qtip-inactive",y)});y()}clearTimeout(t.timers.show);clearTimeout(t.timers.hide);t.timers.show=setTimeout(function(){t.show(z)},t.options.show.delay)}function w(z){if(t.status.disabled===true){return}if(t.options.hide.fixed===true&&t.options.hide.when.event.search(/mouse(out|leave)/i)!==-1&&f(z.relatedTarget).parents("div.qtip[qtip]").length>0){z.stopPropagation();z.preventDefault();clearTimeout(t.timers.hide);return false}clearTimeout(t.timers.show);clearTimeout(t.timers.hide);t.elements.tooltip.stop(true,true);t.timers.hide=setTimeout(function(){t.hide(z)},t.options.hide.delay)}if((t.options.show.when.target.add(t.options.hide.when.target).length===1&&t.options.show.when.event==t.options.hide.when.event&&t.options.hide.when.event!=="inactive")||t.options.hide.when.event=="unfocus"){t.cache.toggle=0;v.bind(t.options.show.when.event+".qtip",function(z){if(t.cache.toggle==0){x(z)}else{w(z)}})}else{v.bind(t.options.show.when.event+".qtip",x);if(t.options.hide.when.event!=="inactive"){u.bind(t.options.hide.when.event+".qtip",w)}}if(t.options.position.type.search(/(fixed|absolute)/)!==-1){t.elements.tooltip.bind("mouseover.qtip",t.focus)}if(t.options.position.target==="mouse"&&t.options.position.type!=="static"){v.bind("mousemove.qtip",function(z){t.cache.mouse={x:z.pageX,y:z.pageY};if(t.status.disabled===false&&t.options.position.adjust.mouse===true&&t.options.position.type!=="static"&&t.elements.tooltip.css("display")!=="none"){t.updatePosition(z)}})}}function o(u,v,A){var z,s,x,y,t,w;z=this;if(A.corner=="center"){return v.position}s=f.extend({},u);y={x:false,y:false};t={left:(s.left<f.fn.qtip.cache.screen.scroll.left),right:(s.left+A.dimensions.width+2>=f.fn.qtip.cache.screen.width+f.fn.qtip.cache.screen.scroll.left),top:(s.top<f.fn.qtip.cache.screen.scroll.top),bottom:(s.top+A.dimensions.height+2>=f.fn.qtip.cache.screen.height+f.fn.qtip.cache.screen.scroll.top)};x={left:(t.left&&(A.corner.search(/right/i)!=-1||(A.corner.search(/right/i)==-1&&!t.right))),right:(t.right&&(A.corner.search(/left/i)!=-1||(A.corner.search(/left/i)==-1&&!t.left))),top:(t.top&&A.corner.search(/top/i)==-1),bottom:(t.bottom&&A.corner.search(/bottom/i)==-1)};if(x.left){if(z.options.position.target!=="mouse"){s.left=v.position.left+v.dimensions.width}else{s.left=z.cache.mouse.x}y.x="Left"}else{if(x.right){if(z.options.position.target!=="mouse"){s.left=v.position.left-A.dimensions.width}else{s.left=z.cache.mouse.x-A.dimensions.width}y.x="Right"}}if(x.top){if(z.options.position.target!=="mouse"){s.top=v.position.top+v.dimensions.height}else{s.top=z.cache.mouse.y}y.y="top"}else{if(x.bottom){if(z.options.position.target!=="mouse"){s.top=v.position.top-A.dimensions.height}else{s.top=z.cache.mouse.y-A.dimensions.height}y.y="bottom"}}if(s.left<0){s.left=u.left;y.x=false}if(s.top<0){s.top=u.top;y.y=false}if(z.options.style.tip.corner!==false){s.corner=new String(A.corner);if(y.x!==false){s.corner=s.corner.replace(/Left|Right|Middle/,y.x)}if(y.y!==false){s.corner=s.corner.replace(/top|bottom/,y.y)}if(s.corner!==z.elements.tip.attr("rel")){e.call(z,s.corner)}}return s}function q(u,t){var v,s;v=f.extend(true,{},u);for(s in v){if(t===true&&s.search(/(tip|classes)/i)!==-1){delete v[s]}else{if(!t&&s.search(/(width|border|tip|title|classes|user)/i)!==-1){delete v[s]}}}return v}function c(s){if(typeof s.tip!=="object"){s.tip={corner:s.tip}}if(typeof s.tip.size!=="object"){s.tip.size={width:s.tip.size,height:s.tip.size}}if(typeof s.border!=="object"){s.border={width:s.border}}if(typeof s.width!=="object"){s.width={value:s.width}}if(typeof s.width.max=="string"){s.width.max=parseInt(s.width.max.replace(/([0-9]+)/i,"$1"))}if(typeof s.width.min=="string"){s.width.min=parseInt(s.width.min.replace(/([0-9]+)/i,"$1"))}if(typeof s.tip.size.x=="number"){s.tip.size.width=s.tip.size.x;delete s.tip.size.x}if(typeof s.tip.size.y=="number"){s.tip.size.height=s.tip.size.y;delete s.tip.size.y}return s}function a(){var s,t,u,x,v,w;s=this;u=[true,{}];for(t=0;t<arguments.length;t++){u.push(arguments[t])}x=[f.extend.apply(f,u)];while(typeof x[0].name=="string"){x.unshift(c(f.fn.qtip.styles[x[0].name]))}x.unshift(true,{classes:{tooltip:"qtip-"+(arguments[0].name||"defaults")}},f.fn.qtip.styles.defaults);v=f.extend.apply(f,x);w=(f.browser.msie)?1:0;v.tip.size.width+=w;v.tip.size.height+=w;if(v.tip.size.width%2>0){v.tip.size.width+=1}if(v.tip.size.height%2>0){v.tip.size.height+=1}if(v.tip.corner===true){v.tip.corner=(s.options.position.corner.tooltip==="center")?false:s.options.position.corner.tooltip}return v}function b(v,u,t){var s={bottomRight:[[0,0],[u,t],[u,0]],bottomLeft:[[0,0],[u,0],[0,t]],topRight:[[0,t],[u,0],[u,t]],topLeft:[[0,0],[0,t],[u,t]],topMiddle:[[0,t],[u/2,0],[u,t]],bottomMiddle:[[0,0],[u,0],[u/2,t]],rightMiddle:[[0,0],[u,t/2],[0,t]],leftMiddle:[[u,0],[u,t],[0,t/2]]};s.leftTop=s.bottomRight;s.rightTop=s.bottomLeft;s.leftBottom=s.topRight;s.rightBottom=s.topLeft;return s[v]}function g(s){var t;if(f("<canvas>").get(0).getContext){t={topLeft:[s,s],topRight:[0,s],bottomLeft:[s,0],bottomRight:[0,0]}}else{if(f.browser.msie){t={topLeft:[-90,90,0],topRight:[-90,90,-s],bottomLeft:[90,270,0],bottomRight:[90,270,-s]}}}return t}function k(){var s,t,u;s=this;u=s.getDimensions();t='<iframe class="qtip-bgiframe" frameborder="0" tabindex="-1" src="javascript:false" style="display:block; position:absolute; z-index:-1; filter:alpha(opacity=\'0\'); border: 1px solid red; height:'+u.height+"px; width:"+u.width+'px" />';s.elements.bgiframe=s.elements.wrapper.prepend(t).children(".qtip-bgiframe:first")}f(document).ready(function(){f.fn.qtip.cache={screen:{scroll:{left:f(window).scrollLeft(),top:f(window).scrollTop()},width:f(window).width(),height:f(window).height()}};var s;f(window).bind("resize scroll",function(t){clearTimeout(s);s=setTimeout(function(){if(t.type==="scroll"){f.fn.qtip.cache.screen.scroll={left:f(window).scrollLeft(),top:f(window).scrollTop()}}else{f.fn.qtip.cache.screen.width=f(window).width();f.fn.qtip.cache.screen.height=f(window).height()}for(i=0;i<f.fn.qtip.interfaces.length;i++){var u=f.fn.qtip.interfaces[i];if(u.status.rendered===true&&(u.options.position.type!=="static"||u.options.position.adjust.scroll&&t.type==="scroll"||u.options.position.adjust.resize&&t.type==="resize")){u.updatePosition(t,true)}}},100)});f(document).bind("mousedown.qtip",function(t){if(f(t.target).parents("div.qtip").length===0){f(".qtip[unfocus]").each(function(){var u=f(this).qtip("api");if(f(this).is(":visible")&&!u.status.disabled&&f(t.target).add(u.elements.target).length>1){u.hide(t)}})}})});f.fn.qtip.interfaces=[];f.fn.qtip.log={error:function(){return this}};f.fn.qtip.constants={};f.fn.qtip.defaults={content:{prerender:false,text:false,url:false,data:null,title:{text:false,button:false}},position:{target:false,corner:{target:"bottomRight",tooltip:"topLeft"},adjust:{x:0,y:0,mouse:true,screen:false,scroll:true,resize:true},type:"absolute",container:false},show:{when:{target:false,event:"mouseover"},effect:{type:"fade",length:100},delay:140,solo:false,ready:false},hide:{when:{target:false,event:"mouseout"},effect:{type:"fade",length:100},delay:0,fixed:false},api:{beforeRender:function(){},onRender:function(){},beforePositionUpdate:function(){},onPositionUpdate:function(){},beforeShow:function(){},onShow:function(){},beforeHide:function(){},onHide:function(){},beforeContentUpdate:function(){},onContentUpdate:function(){},beforeContentLoad:function(){},onContentLoad:function(){},beforeTitleUpdate:function(){},onTitleUpdate:function(){},beforeDestroy:function(){},onDestroy:function(){},beforeFocus:function(){},onFocus:function(){}}};f.fn.qtip.styles={defaults:{background:"white",color:"#111",overflow:"hidden",textAlign:"left",width:{min:0,max:250},padding:"5px 9px",border:{width:1,radius:0,color:"#d3d3d3"},tip:{corner:false,color:false,size:{width:13,height:13},opacity:1},title:{background:"#e1e1e1",fontWeight:"bold",padding:"7px 12px"},button:{cursor:"pointer"},classes:{target:"",tip:"qtip-tip",title:"qtip-title",button:"qtip-button",content:"qtip-content",active:"qtip-active"}},cream:{border:{width:3,radius:0,color:"#F9E98E"},title:{background:"#F0DE7D",color:"#A27D35"},background:"#FBF7AA",color:"#A27D35",classes:{tooltip:"qtip-cream"}},light:{border:{width:3,radius:0,color:"#E2E2E2"},title:{background:"#f1f1f1",color:"#454545"},background:"white",color:"#454545",classes:{tooltip:"qtip-light"}},dark:{border:{width:3,radius:0,color:"#303030"},title:{background:"#404040",color:"#f3f3f3"},background:"#505050",color:"#f3f3f3",classes:{tooltip:"qtip-dark"}},red:{border:{width:3,radius:0,color:"#CE6F6F"},title:{background:"#f28279",color:"#9C2F2F"},background:"#F79992",color:"#9C2F2F",classes:{tooltip:"qtip-red"}},green:{border:{width:3,radius:0,color:"#A9DB66"},title:{background:"#b9db8c",color:"#58792E"},background:"#CDE6AC",color:"#58792E",classes:{tooltip:"qtip-green"}},blue:{border:{width:3,radius:0,color:"#ADD9ED"},title:{background:"#D0E9F5",color:"#5E99BD"},background:"#E5F6FE",color:"#4D9FBF",classes:{tooltip:"qtip-blue"}}}})(jQuery);
/* jquery.sparkline 1.6 - http://omnipotent.net/jquery.sparkline/ 
** Licensed under the New BSD License - see above site for details */

(function($){var defaults={common:{type:'line',lineColor:'#00f',fillColor:'#cdf',defaultPixelsPerValue:3,width:'auto',height:'auto',composite:false,tagValuesAttribute:'values',tagOptionsPrefix:'spark',enableTagOptions:false},line:{spotColor:'#f80',spotRadius:1.5,minSpotColor:'#f80',maxSpotColor:'#f80',lineWidth:1,normalRangeMin:undefined,normalRangeMax:undefined,normalRangeColor:'#ccc',drawNormalOnTop:false,chartRangeMin:undefined,chartRangeMax:undefined,chartRangeMinX:undefined,chartRangeMaxX:undefined},bar:{barColor:'#00f',negBarColor:'#f44',zeroColor:undefined,nullColor:undefined,zeroAxis:undefined,barWidth:4,barSpacing:1,chartRangeMax:undefined,chartRangeMin:undefined,chartRangeClip:false,colorMap:undefined},tristate:{barWidth:4,barSpacing:1,posBarColor:'#6f6',negBarColor:'#f44',zeroBarColor:'#999',colorMap:{}},discrete:{lineHeight:'auto',thresholdColor:undefined,thresholdValue:0,chartRangeMax:undefined,chartRangeMin:undefined,chartRangeClip:false},bullet:{targetColor:'red',targetWidth:3,performanceColor:'blue',rangeColors:['#D3DAFE','#A8B6FF','#7F94FF'],base:undefined},pie:{sliceColors:['#f00','#0f0','#00f']},box:{raw:false,boxLineColor:'black',boxFillColor:'#cdf',whiskerColor:'black',outlierLineColor:'#333',outlierFillColor:'white',medianColor:'red',showOutliers:true,outlierIQR:1.5,spotRadius:1.5,target:undefined,targetColor:'#4a2',chartRangeMax:undefined,chartRangeMin:undefined}};var VCanvas_base,VCanvas_canvas,VCanvas_vml;$.fn.simpledraw=function(width,height,use_existing){if(use_existing&&this[0].VCanvas){return this[0].VCanvas;}
if(width===undefined){width=$(this).innerWidth();}
if(height===undefined){height=$(this).innerHeight();}
if($.browser.hasCanvas){return new VCanvas_canvas(width,height,this);}else if($.browser.msie){return new VCanvas_vml(width,height,this);}else{return false;}};var pending=[];$.fn.sparkline=function(uservalues,userOptions){return this.each(function(){var options=new $.fn.sparkline.options(this,userOptions);var render=function(){var values,width,height;if(uservalues==='html'||uservalues===undefined){var vals=this.getAttribute(options.get('tagValuesAttribute'));if(vals===undefined||vals===null){vals=$(this).html();}
values=vals.replace(/(^\s*<!--)|(-->\s*$)|\s+/g,'').split(',');}else{values=uservalues;}
width=options.get('width')=='auto'?values.length*options.get('defaultPixelsPerValue'):options.get('width');if(options.get('height')=='auto'){if(!options.get('composite')||!this.VCanvas){var tmp=document.createElement('span');tmp.innerHTML='a';$(this).html(tmp);height=$(tmp).innerHeight();$(tmp).remove();}}else{height=options.get('height');}
$.fn.sparkline[options.get('type')].call(this,values,options,width,height);};if(($(this).html()&&$(this).is(':hidden'))||($.fn.jquery<"1.3.0"&&$(this).parents().is(':hidden'))||!$(this).parents('body').length){pending.push([this,render]);}else{render.call(this);}});};$.fn.sparkline.defaults=defaults;$.sparkline_display_visible=function(){for(var i=pending.length-1;i>=0;i--){var el=pending[i][0];if($(el).is(':visible')&&!$(el).parents().is(':hidden')){pending[i][1].call(el);pending.splice(i,1);}}};var UNSET_OPTION={};var normalizeValue=function(val){switch(val){case'undefined':val=undefined;break;case'null':val=null;break;case'true':val=true;break;case'false':val=false;break;default:var nf=parseFloat(val);if(val==nf){val=nf;}}
return val;};$.fn.sparkline.options=function(tag,userOptions){var extendedOptions;this.userOptions=userOptions=userOptions||{};this.tag=tag;this.tagValCache={};var defaults=$.fn.sparkline.defaults;var base=defaults.common;this.tagOptionsPrefix=userOptions.enableTagOptions&&(userOptions.tagOptionsPrefix||base.tagOptionsPrefix);var tagOptionType=this.getTagSetting('type');if(tagOptionType===UNSET_OPTION){extendedOptions=defaults[userOptions.type||base.type];}else{extendedOptions=defaults[tagOptionType];}
this.mergedOptions=$.extend({},base,extendedOptions,userOptions);};$.fn.sparkline.options.prototype.getTagSetting=function(key){var val,i,prefix=this.tagOptionsPrefix;if(prefix===false||prefix===undefined){return UNSET_OPTION;}
if(this.tagValCache.hasOwnProperty(key)){val=this.tagValCache.key;}else{val=this.tag.getAttribute(prefix+key);if(val===undefined||val===null){val=UNSET_OPTION;}else if(val.substr(0,1)=='['){val=val.substr(1,val.length-2).split(',');for(i=val.length;i--;){val[i]=normalizeValue(val[i].replace(/(^\s*)|(\s*$)/g,''));}}else if(val.substr(0,1)=='{'){var pairs=val.substr(1,val.length-2).split(',');val={};for(i=pairs.length;i--;){var keyval=pairs[i].split(':',2);val[keyval[0].replace(/(^\s*)|(\s*$)/g,'')]=normalizeValue(keyval[1].replace(/(^\s*)|(\s*$)/g,''));}}else{val=normalizeValue(val);}
this.tagValCache.key=val;}
return val;};$.fn.sparkline.options.prototype.get=function(key){var tagOption=this.getTagSetting(key);if(tagOption!==UNSET_OPTION){return tagOption;}
return this.mergedOptions[key];};$.fn.sparkline.line=function(values,options,width,height){var xvalues=[],yvalues=[],yminmax=[];for(var i=0;i<values.length;i++){var val=values[i];var isstr=typeof(values[i])=='string';var isarray=typeof(values[i])=='object'&&values[i]instanceof Array;var sp=isstr&&values[i].split(':');if(isstr&&sp.length==2){xvalues.push(Number(sp[0]));yvalues.push(Number(sp[1]));yminmax.push(Number(sp[1]));}else if(isarray){xvalues.push(val[0]);yvalues.push(val[1]);yminmax.push(val[1]);}else{xvalues.push(i);if(values[i]===null||values[i]=='null'){yvalues.push(null);}else{yvalues.push(Number(val));yminmax.push(Number(val));}}}
if(options.get('xvalues')){xvalues=options.get('xvalues');}
var maxy=Math.max.apply(Math,yminmax);var maxyval=maxy;var miny=Math.min.apply(Math,yminmax);var minyval=miny;var maxx=Math.max.apply(Math,xvalues);var minx=Math.min.apply(Math,xvalues);var normalRangeMin=options.get('normalRangeMin');var normalRangeMax=options.get('normalRangeMax');if(normalRangeMin!==undefined){if(normalRangeMin<miny){miny=normalRangeMin;}
if(normalRangeMax>maxy){maxy=normalRangeMax;}}
if(options.get('chartRangeMin')!==undefined&&(options.get('chartRangeClip')||options.get('chartRangeMin')<miny)){miny=options.get('chartRangeMin');}
if(options.get('chartRangeMax')!==undefined&&(options.get('chartRangeClip')||options.get('chartRangeMax')>maxy)){maxy=options.get('chartRangeMax');}
if(options.get('chartRangeMinX')!==undefined&&(options.get('chartRangeClipX')||options.get('chartRangeMinX')<minx)){minx=options.get('chartRangeMinX');}
if(options.get('chartRangeMaxX')!==undefined&&(options.get('chartRangeClipX')||options.get('chartRangeMaxX')>maxx)){maxx=options.get('chartRangeMaxX');}
var rangex=maxx-minx===0?1:maxx-minx;var rangey=maxy-miny===0?1:maxy-miny;var vl=yvalues.length-1;if(vl<1){this.innerHTML='';return;}
var target=$(this).simpledraw(width,height,options.get('composite'));if(target){var canvas_width=target.pixel_width;var canvas_height=target.pixel_height;var canvas_top=0;var canvas_left=0;var spotRadius=options.get('spotRadius');if(spotRadius&&(canvas_width<(spotRadius*4)||canvas_height<(spotRadius*4))){spotRadius=0;}
if(spotRadius){if(options.get('minSpotColor')||(options.get('spotColor')&&yvalues[vl]==miny)){canvas_height-=Math.ceil(spotRadius);}
if(options.get('maxSpotColor')||(options.get('spotColor')&&yvalues[vl]==maxy)){canvas_height-=Math.ceil(spotRadius);canvas_top+=Math.ceil(spotRadius);}
if(options.get('minSpotColor')||options.get('maxSpotColor')&&(yvalues[0]==miny||yvalues[0]==maxy)){canvas_left+=Math.ceil(spotRadius);canvas_width-=Math.ceil(spotRadius);}
if(options.get('spotColor')||(options.get('minSpotColor')||options.get('maxSpotColor')&&(yvalues[vl]==miny||yvalues[vl]==maxy))){canvas_width-=Math.ceil(spotRadius);}}
canvas_height--;var drawNormalRange=function(){if(normalRangeMin!==undefined){var ytop=canvas_top+Math.round(canvas_height-(canvas_height*((normalRangeMax-miny)/rangey)));var height=Math.round((canvas_height*(normalRangeMax-normalRangeMin))/rangey);target.drawRect(canvas_left,ytop,canvas_width,height,undefined,options.get('normalRangeColor'));}};if(!options.get('drawNormalOnTop')){drawNormalRange();}
var path=[];var paths=[path];var x,y,vlen=yvalues.length;for(i=0;i<vlen;i++){x=xvalues[i];y=yvalues[i];if(y===null){if(i){if(yvalues[i-1]!==null){path=[];paths.push(path);}}}else{if(y<miny){y=miny;}
if(y>maxy){y=maxy;}
if(!path.length){path.push([canvas_left+Math.round((x-minx)*(canvas_width/rangex)),canvas_top+canvas_height]);}
path.push([canvas_left+Math.round((x-minx)*(canvas_width/rangex)),canvas_top+Math.round(canvas_height-(canvas_height*((y-miny)/rangey)))]);}}
var lineshapes=[];var fillshapes=[];var plen=paths.length;for(i=0;i<plen;i++){path=paths[i];if(!path.length){continue;}
if(options.get('fillColor')){path.push([path[path.length-1][0],canvas_top+canvas_height-1]);fillshapes.push(path.slice(0));path.pop();}
if(path.length>2){path[0]=[path[0][0],path[1][1]];}
lineshapes.push(path);}
plen=fillshapes.length;for(i=0;i<plen;i++){target.drawShape(fillshapes[i],undefined,options.get('fillColor'));}
if(options.get('drawNormalOnTop')){drawNormalRange();}
plen=lineshapes.length;for(i=0;i<plen;i++){target.drawShape(lineshapes[i],options.get('lineColor'),undefined,options.get('lineWidth'));}
if(spotRadius&&options.get('spotColor')){target.drawCircle(canvas_left+Math.round(xvalues[xvalues.length-1]*(canvas_width/rangex)),canvas_top+Math.round(canvas_height-(canvas_height*((yvalues[vl]-miny)/rangey))),spotRadius,undefined,options.get('spotColor'));}
if(maxy!=minyval){if(spotRadius&&options.get('minSpotColor')){x=xvalues[$.inArray(minyval,yvalues)];target.drawCircle(canvas_left+Math.round((x-minx)*(canvas_width/rangex)),canvas_top+Math.round(canvas_height-(canvas_height*((minyval-miny)/rangey))),spotRadius,undefined,options.get('minSpotColor'));}
if(spotRadius&&options.get('maxSpotColor')){x=xvalues[$.inArray(maxyval,yvalues)];target.drawCircle(canvas_left+Math.round((x-minx)*(canvas_width/rangex)),canvas_top+Math.round(canvas_height-(canvas_height*((maxyval-miny)/rangey))),spotRadius,undefined,options.get('maxSpotColor'));}}}else{this.innerHTML='';}};$.fn.sparkline.bar=function(values,options,width,height){width=(values.length*options.get('barWidth'))+((values.length-1)*options.get('barSpacing'));var num_values=[];for(var i=0,vlen=values.length;i<vlen;i++){if(values[i]=='null'||values[i]===null){values[i]=null;}else{values[i]=Number(values[i]);num_values.push(Number(values[i]));}}
var max=Math.max.apply(Math,num_values),min=Math.min.apply(Math,num_values);if(options.get('chartRangeMin')!==undefined&&(options.get('chartRangeClip')||options.get('chartRangeMin')<min)){min=options.get('chartRangeMin');}
if(options.get('chartRangeMax')!==undefined&&(options.get('chartRangeClip')||options.get('chartRangeMax')>max)){max=options.get('chartRangeMax');}
var zeroAxis=options.get('zeroAxis');if(zeroAxis===undefined){zeroAxis=min<0;}
var range=max-min===0?1:max-min;var colorMapByIndex,colorMapByValue;if($.isArray(options.get('colorMap'))){colorMapByIndex=options.get('colorMap');colorMapByValue=null;}else{colorMapByIndex=null;colorMapByValue=options.get('colorMap');}
var target=$(this).simpledraw(width,height,options.get('composite'));if(target){var color,canvas_height=target.pixel_height,yzero=min<0&&zeroAxis?canvas_height-Math.round(canvas_height*(Math.abs(min)/range))-1:canvas_height-1;for(i=values.length;i--;){var x=i*(options.get('barWidth')+options.get('barSpacing')),y,val=values[i];if(val===null){if(options.get('nullColor')){color=options.get('nullColor');val=(zeroAxis&&min<0)?0:min;height=1;y=(zeroAxis&&min<0)?yzero:canvas_height-height;}else{continue;}}else{if(val<min){val=min;}
if(val>max){val=max;}
color=(val<0)?options.get('negBarColor'):options.get('barColor');if(zeroAxis&&min<0){height=Math.round(canvas_height*((Math.abs(val)/range)))+1;y=(val<0)?yzero:yzero-height;}else{height=Math.round(canvas_height*((val-min)/range))+1;y=canvas_height-height;}
if(val===0&&options.get('zeroColor')!==undefined){color=options.get('zeroColor');}
if(colorMapByValue&&colorMapByValue[val]){color=colorMapByValue[val];}else if(colorMapByIndex&&colorMapByIndex.length>i){color=colorMapByIndex[i];}
if(color===null){continue;}}
target.drawRect(x,y,options.get('barWidth')-1,height-1,color,color);}}else{this.innerHTML='';}};$.fn.sparkline.tristate=function(values,options,width,height){values=$.map(values,Number);width=(values.length*options.get('barWidth'))+((values.length-1)*options.get('barSpacing'));var colorMapByIndex,colorMapByValue;if($.isArray(options.get('colorMap'))){colorMapByIndex=options.get('colorMap');colorMapByValue=null;}else{colorMapByIndex=null;colorMapByValue=options.get('colorMap');}
var target=$(this).simpledraw(width,height,options.get('composite'));if(target){var canvas_height=target.pixel_height,half_height=Math.round(canvas_height/2);for(var i=values.length;i--;){var x=i*(options.get('barWidth')+options.get('barSpacing')),y,color;if(values[i]<0){y=half_height;height=half_height-1;color=options.get('negBarColor');}else if(values[i]>0){y=0;height=half_height-1;color=options.get('posBarColor');}else{y=half_height-1;height=2;color=options.get('zeroBarColor');}
if(colorMapByValue&&colorMapByValue[values[i]]){color=colorMapByValue[values[i]];}else if(colorMapByIndex&&colorMapByIndex.length>i){color=colorMapByIndex[i];}
if(color===null){continue;}
target.drawRect(x,y,options.get('barWidth')-1,height-1,color,color);}}else{this.innerHTML='';}};$.fn.sparkline.discrete=function(values,options,width,height){values=$.map(values,Number);width=options.get('width')=='auto'?values.length*2:width;var interval=Math.floor(width/values.length);var target=$(this).simpledraw(width,height,options.get('composite'));if(target){var canvas_height=target.pixel_height,line_height=options.get('lineHeight')=='auto'?Math.round(canvas_height*0.3):options.get('lineHeight'),pheight=canvas_height-line_height,min=Math.min.apply(Math,values),max=Math.max.apply(Math,values);if(options.get('chartRangeMin')!==undefined&&(options.get('chartRangeClip')||options.get('chartRangeMin')<min)){min=options.get('chartRangeMin');}
if(options.get('chartRangeMax')!==undefined&&(options.get('chartRangeClip')||options.get('chartRangeMax')>max)){max=options.get('chartRangeMax');}
var range=max-min;for(var i=values.length;i--;){var val=values[i];if(val<min){val=min;}
if(val>max){val=max;}
var x=(i*interval),ytop=Math.round(pheight-pheight*((val-min)/range));target.drawLine(x,ytop,x,ytop+line_height,(options.get('thresholdColor')&&val<options.get('thresholdValue'))?options.get('thresholdColor'):options.get('lineColor'));}}else{this.innerHTML='';}};$.fn.sparkline.bullet=function(values,options,width,height){values=$.map(values,Number);width=options.get('width')=='auto'?'4.0em':width;var target=$(this).simpledraw(width,height,options.get('composite'));if(target&&values.length>1){var canvas_width=target.pixel_width-Math.ceil(options.get('targetWidth')/2),canvas_height=target.pixel_height,min=Math.min.apply(Math,values),max=Math.max.apply(Math,values);if(options.get('base')===undefined){min=min<0?min:0;}else{min=options.get('base');}
var range=max-min;for(var i=2,vlen=values.length;i<vlen;i++){var rangeval=values[i],rangewidth=Math.round(canvas_width*((rangeval-min)/range));target.drawRect(0,0,rangewidth-1,canvas_height-1,options.get('rangeColors')[i-2],options.get('rangeColors')[i-2]);}
var perfval=values[1],perfwidth=Math.round(canvas_width*((perfval-min)/range));target.drawRect(0,Math.round(canvas_height*0.3),perfwidth-1,Math.round(canvas_height*0.4)-1,options.get('performanceColor'),options.get('performanceColor'));var targetval=values[0],x=Math.round(canvas_width*((targetval-min)/range)-(options.get('targetWidth')/2)),targettop=Math.round(canvas_height*0.10),targetheight=canvas_height-(targettop*2);target.drawRect(x,targettop,options.get('targetWidth')-1,targetheight-1,options.get('targetColor'),options.get('targetColor'));}else{this.innerHTML='';}};$.fn.sparkline.pie=function(values,options,width,height){values=$.map(values,Number);width=options.get('width')=='auto'?height:width;var target=$(this).simpledraw(width,height,options.get('composite'));if(target&&values.length>1){var canvas_width=target.pixel_width,canvas_height=target.pixel_height,radius=Math.floor(Math.min(canvas_width,canvas_height)/2),total=0,next=0,circle=2*Math.PI;for(var i=values.length;i--;){total+=values[i];}
if(options.get('offset')){next+=(2*Math.PI)*(options.get('offset')/360);}
var vlen=values.length;for(i=0;i<vlen;i++){var start=next;var end=next;if(total>0){end=next+(circle*(values[i]/total));}
target.drawPieSlice(radius,radius,radius,start,end,undefined,options.get('sliceColors')[i%options.get('sliceColors').length]);next=end;}}};var quartile=function(values,q){if(q==2){var vl2=Math.floor(values.length/2);return values.length%2?values[vl2]:(values[vl2]+values[vl2+1])/2;}else{var vl4=Math.floor(values.length/4);return values.length%2?(values[vl4*q]+values[vl4*q+1])/2:values[vl4*q];}};$.fn.sparkline.box=function(values,options,width,height){values=$.map(values,Number);width=options.get('width')=='auto'?'4.0em':width;var minvalue=options.get('chartRangeMin')===undefined?Math.min.apply(Math,values):options.get('chartRangeMin'),maxvalue=options.get('chartRangeMax')===undefined?Math.max.apply(Math,values):options.get('chartRangeMax'),target=$(this).simpledraw(width,height,options.get('composite')),vlen=values.length,lwhisker,loutlier,q1,q2,q3,rwhisker,routlier;if(target&&values.length>1){var canvas_width=target.pixel_width,canvas_height=target.pixel_height;if(options.get('raw')){if(options.get('showOutliers')&&values.length>5){loutlier=values[0];lwhisker=values[1];q1=values[2];q2=values[3];q3=values[4];rwhisker=values[5];routlier=values[6];}else{lwhisker=values[0];q1=values[1];q2=values[2];q3=values[3];rwhisker=values[4];}}else{values.sort(function(a,b){return a-b;});q1=quartile(values,1);q2=quartile(values,2);q3=quartile(values,3);var iqr=q3-q1;if(options.get('showOutliers')){lwhisker=undefined;rwhisker=undefined;for(var i=0;i<vlen;i++){if(lwhisker===undefined&&values[i]>q1-(iqr*options.get('outlierIQR'))){lwhisker=values[i];}
if(values[i]<q3+(iqr*options.get('outlierIQR'))){rwhisker=values[i];}}
loutlier=values[0];routlier=values[vlen-1];}else{lwhisker=values[0];rwhisker=values[vlen-1];}}
var unitsize=canvas_width/(maxvalue-minvalue+1),canvas_left=0;if(options.get('showOutliers')){canvas_left=Math.ceil(options.get('spotRadius'));canvas_width-=2*Math.ceil(options.get('spotRadius'));unitsize=canvas_width/(maxvalue-minvalue+1);if(loutlier<lwhisker){target.drawCircle((loutlier-minvalue)*unitsize+canvas_left,canvas_height/2,options.get('spotRadius'),options.get('outlierLineColor'),options.get('outlierFillColor'));}
if(routlier>rwhisker){target.drawCircle((routlier-minvalue)*unitsize+canvas_left,canvas_height/2,options.get('spotRadius'),options.get('outlierLineColor'),options.get('outlierFillColor'));}}
target.drawRect(Math.round((q1-minvalue)*unitsize+canvas_left),Math.round(canvas_height*0.1),Math.round((q3-q1)*unitsize),Math.round(canvas_height*0.8),options.get('boxLineColor'),options.get('boxFillColor'));target.drawLine(Math.round((lwhisker-minvalue)*unitsize+canvas_left),Math.round(canvas_height/2),Math.round((q1-minvalue)*unitsize+canvas_left),Math.round(canvas_height/2),options.get('lineColor'));target.drawLine(Math.round((lwhisker-minvalue)*unitsize+canvas_left),Math.round(canvas_height/4),Math.round((lwhisker-minvalue)*unitsize+canvas_left),Math.round(canvas_height-canvas_height/4),options.get('whiskerColor'));target.drawLine(Math.round((rwhisker-minvalue)*unitsize+canvas_left),Math.round(canvas_height/2),Math.round((q3-minvalue)*unitsize+canvas_left),Math.round(canvas_height/2),options.get('lineColor'));target.drawLine(Math.round((rwhisker-minvalue)*unitsize+canvas_left),Math.round(canvas_height/4),Math.round((rwhisker-minvalue)*unitsize+canvas_left),Math.round(canvas_height-canvas_height/4),options.get('whiskerColor'));target.drawLine(Math.round((q2-minvalue)*unitsize+canvas_left),Math.round(canvas_height*0.1),Math.round((q2-minvalue)*unitsize+canvas_left),Math.round(canvas_height*0.9),options.get('medianColor'));if(options.get('target')){var size=Math.ceil(options.get('spotRadius'));target.drawLine(Math.round((options.get('target')-minvalue)*unitsize+canvas_left),Math.round((canvas_height/2)-size),Math.round((options.get('target')-minvalue)*unitsize+canvas_left),Math.round((canvas_height/2)+size),options.get('targetColor'));target.drawLine(Math.round((options.get('target')-minvalue)*unitsize+canvas_left-size),Math.round(canvas_height/2),Math.round((options.get('target')-minvalue)*unitsize+canvas_left+size),Math.round(canvas_height/2),options.get('targetColor'));}}else{this.innerHTML='';}};if($.browser.msie&&!document.namespaces.v){document.namespaces.add('v','urn:schemas-microsoft-com:vml','#default#VML');}
if($.browser.hasCanvas===undefined){var t=document.createElement('canvas');$.browser.hasCanvas=t.getContext!==undefined;}
VCanvas_base=function(width,height,target){};VCanvas_base.prototype={init:function(width,height,target){this.width=width;this.height=height;this.target=target;if(target[0]){target=target[0];}
target.VCanvas=this;},drawShape:function(path,lineColor,fillColor,lineWidth){alert('drawShape not implemented');},drawLine:function(x1,y1,x2,y2,lineColor,lineWidth){return this.drawShape([[x1,y1],[x2,y2]],lineColor,lineWidth);},drawCircle:function(x,y,radius,lineColor,fillColor){alert('drawCircle not implemented');},drawPieSlice:function(x,y,radius,startAngle,endAngle,lineColor,fillColor){alert('drawPieSlice not implemented');},drawRect:function(x,y,width,height,lineColor,fillColor){alert('drawRect not implemented');},getElement:function(){return this.canvas;},_insert:function(el,target){$(target).html(el);}};VCanvas_canvas=function(width,height,target){return this.init(width,height,target);};VCanvas_canvas.prototype=$.extend(new VCanvas_base(),{_super:VCanvas_base.prototype,init:function(width,height,target){this._super.init(width,height,target);this.canvas=document.createElement('canvas');if(target[0]){target=target[0];}
target.VCanvas=this;$(this.canvas).css({display:'inline-block',width:width,height:height,verticalAlign:'top'});this._insert(this.canvas,target);this.pixel_height=$(this.canvas).height();this.pixel_width=$(this.canvas).width();this.canvas.width=this.pixel_width;this.canvas.height=this.pixel_height;$(this.canvas).css({width:this.pixel_width,height:this.pixel_height});},_getContext:function(lineColor,fillColor,lineWidth){var context=this.canvas.getContext('2d');if(lineColor!==undefined){context.strokeStyle=lineColor;}
context.lineWidth=lineWidth===undefined?1:lineWidth;if(fillColor!==undefined){context.fillStyle=fillColor;}
return context;},drawShape:function(path,lineColor,fillColor,lineWidth){var context=this._getContext(lineColor,fillColor,lineWidth);context.beginPath();context.moveTo(path[0][0]+0.5,path[0][1]+0.5);for(var i=1,plen=path.length;i<plen;i++){context.lineTo(path[i][0]+0.5,path[i][1]+0.5);}
if(lineColor!==undefined){context.stroke();}
if(fillColor!==undefined){context.fill();}},drawCircle:function(x,y,radius,lineColor,fillColor){var context=this._getContext(lineColor,fillColor);context.beginPath();context.arc(x,y,radius,0,2*Math.PI,false);if(lineColor!==undefined){context.stroke();}
if(fillColor!==undefined){context.fill();}},drawPieSlice:function(x,y,radius,startAngle,endAngle,lineColor,fillColor){var context=this._getContext(lineColor,fillColor);context.beginPath();context.moveTo(x,y);context.arc(x,y,radius,startAngle,endAngle,false);context.lineTo(x,y);context.closePath();if(lineColor!==undefined){context.stroke();}
if(fillColor){context.fill();}},drawRect:function(x,y,width,height,lineColor,fillColor){return this.drawShape([[x,y],[x+width,y],[x+width,y+height],[x,y+height],[x,y]],lineColor,fillColor);}});VCanvas_vml=function(width,height,target){return this.init(width,height,target);};VCanvas_vml.prototype=$.extend(new VCanvas_base(),{_super:VCanvas_base.prototype,init:function(width,height,target){this._super.init(width,height,target);if(target[0]){target=target[0];}
target.VCanvas=this;this.canvas=document.createElement('span');$(this.canvas).css({display:'inline-block',position:'relative',overflow:'hidden',width:width,height:height,margin:'0px',padding:'0px',verticalAlign:'top'});this._insert(this.canvas,target);this.pixel_height=$(this.canvas).height();this.pixel_width=$(this.canvas).width();this.canvas.width=this.pixel_width;this.canvas.height=this.pixel_height;var groupel='<v:group coordorigin="0 0" coordsize="'+this.pixel_width+' '+this.pixel_height+'"'+' style="position:absolute;top:0;left:0;width:'+this.pixel_width+'px;height='+this.pixel_height+'px;"></v:group>';this.canvas.insertAdjacentHTML('beforeEnd',groupel);this.group=$(this.canvas).children()[0];},drawShape:function(path,lineColor,fillColor,lineWidth){var vpath=[];for(var i=0,plen=path.length;i<plen;i++){vpath[i]=''+(path[i][0])+','+(path[i][1]);}
var initial=vpath.splice(0,1);lineWidth=lineWidth===undefined?1:lineWidth;var stroke=lineColor===undefined?' stroked="false" ':' strokeWeight="'+lineWidth+'" strokeColor="'+lineColor+'" ';var fill=fillColor===undefined?' filled="false"':' fillColor="'+fillColor+'" filled="true" ';var closed=vpath[0]==vpath[vpath.length-1]?'x ':'';var vel='<v:shape coordorigin="0 0" coordsize="'+this.pixel_width+' '+this.pixel_height+'" '+
stroke+
fill+' style="position:absolute;left:0px;top:0px;height:'+this.pixel_height+'px;width:'+this.pixel_width+'px;padding:0px;margin:0px;" '+' path="m '+initial+' l '+vpath.join(', ')+' '+closed+'e">'+' </v:shape>';this.group.insertAdjacentHTML('beforeEnd',vel);},drawCircle:function(x,y,radius,lineColor,fillColor){x-=radius+1;y-=radius+1;var stroke=lineColor===undefined?' stroked="false" ':' strokeWeight="1" strokeColor="'+lineColor+'" ';var fill=fillColor===undefined?' filled="false"':' fillColor="'+fillColor+'" filled="true" ';var vel='<v:oval '+
stroke+
fill+' style="position:absolute;top:'+y+'px; left:'+x+'px; width:'+(radius*2)+'px; height:'+(radius*2)+'px"></v:oval>';this.group.insertAdjacentHTML('beforeEnd',vel);},drawPieSlice:function(x,y,radius,startAngle,endAngle,lineColor,fillColor){if(startAngle==endAngle){return;}
if((endAngle-startAngle)==(2*Math.PI)){startAngle=0.0;endAngle=(2*Math.PI);}
var startx=x+Math.round(Math.cos(startAngle)*radius);var starty=y+Math.round(Math.sin(startAngle)*radius);var endx=x+Math.round(Math.cos(endAngle)*radius);var endy=y+Math.round(Math.sin(endAngle)*radius);if(startx==endx&&starty==endy&&(endAngle-startAngle)<Math.PI){return;}
var vpath=[x-radius,y-radius,x+radius,y+radius,startx,starty,endx,endy];var stroke=lineColor===undefined?' stroked="false" ':' strokeWeight="1" strokeColor="'+lineColor+'" ';var fill=fillColor===undefined?' filled="false"':' fillColor="'+fillColor+'" filled="true" ';var vel='<v:shape coordorigin="0 0" coordsize="'+this.pixel_width+' '+this.pixel_height+'" '+
stroke+
fill+' style="position:absolute;left:0px;top:0px;height:'+this.pixel_height+'px;width:'+this.pixel_width+'px;padding:0px;margin:0px;" '+' path="m '+x+','+y+' wa '+vpath.join(', ')+' x e">'+' </v:shape>';this.group.insertAdjacentHTML('beforeEnd',vel);},drawRect:function(x,y,width,height,lineColor,fillColor){return this.drawShape([[x,y],[x,y+height],[x+width,y+height],[x+width,y],[x,y]],lineColor,fillColor);}});})(jQuery);

(function($){$.extend({tablesorter:new
function(){var parsers=[],widgets=[];this.defaults={cssHeader:"header",cssAsc:"headerSortUp",cssDesc:"headerSortDown",cssChildRow:"expand-child",sortInitialOrder:"asc",sortMultiSortKey:"shiftKey",sortForce:null,sortAppend:null,sortLocaleCompare:true,textExtraction:"simple",parsers:{},widgets:[],widgetZebra:{css:["even","odd"]},headers:{},widthFixed:false,cancelSelection:true,sortList:[],headerList:[],dateFormat:"us",decimal:'/\.|\,/g',onRenderHeader:null,selectorHeaders:'thead th',debug:false};function benchmark(s,d){log(s+","+(new Date().getTime()-d.getTime())+"ms");}this.benchmark=benchmark;function log(s){if(typeof console!="undefined"&&typeof console.debug!="undefined"){console.log(s);}else{alert(s);}}function buildParserCache(table,$headers){if(table.config.debug){var parsersDebug="";}if(table.tBodies.length==0)return;var rows=table.tBodies[0].rows;if(rows[0]){var list=[],cells=rows[0].cells,l=cells.length;for(var i=0;i<l;i++){var p=false;if($.metadata&&($($headers[i]).metadata()&&$($headers[i]).metadata().sorter)){p=getParserById($($headers[i]).metadata().sorter);}else if((table.config.headers[i]&&table.config.headers[i].sorter)){p=getParserById(table.config.headers[i].sorter);}if(!p){p=detectParserForColumn(table,rows,-1,i);}if(table.config.debug){parsersDebug+="column:"+i+" parser:"+p.id+"\n";}list.push(p);}}if(table.config.debug){log(parsersDebug);}return list;};function detectParserForColumn(table,rows,rowIndex,cellIndex){var l=parsers.length,node=false,nodeValue=false,keepLooking=true;while(nodeValue==''&&keepLooking){rowIndex++;if(rows[rowIndex]){node=getNodeFromRowAndCellIndex(rows,rowIndex,cellIndex);nodeValue=trimAndGetNodeText(table.config,node);if(table.config.debug){log('Checking if value was empty on row:'+rowIndex);}}else{keepLooking=false;}}for(var i=1;i<l;i++){if(parsers[i].is(nodeValue,table,node)){return parsers[i];}}return parsers[0];}function getNodeFromRowAndCellIndex(rows,rowIndex,cellIndex){return rows[rowIndex].cells[cellIndex];}function trimAndGetNodeText(config,node){return $.trim(getElementText(config,node));}function getParserById(name){var l=parsers.length;for(var i=0;i<l;i++){if(parsers[i].id.toLowerCase()==name.toLowerCase()){return parsers[i];}}return false;}function buildCache(table){if(table.config.debug){var cacheTime=new Date();}var totalRows=(table.tBodies[0]&&table.tBodies[0].rows.length)||0,totalCells=(table.tBodies[0].rows[0]&&table.tBodies[0].rows[0].cells.length)||0,parsers=table.config.parsers,cache={row:[],normalized:[]};for(var i=0;i<totalRows;++i){var c=$(table.tBodies[0].rows[i]),cols=[];if(c.hasClass(table.config.cssChildRow)){cache.row[cache.row.length-1]=cache.row[cache.row.length-1].add(c);continue;}cache.row.push(c);for(var j=0;j<totalCells;++j){cols.push(parsers[j].format(getElementText(table.config,c[0].cells[j]),table,c[0].cells[j]));}cols.push(cache.normalized.length);cache.normalized.push(cols);cols=null;};if(table.config.debug){benchmark("Building cache for "+totalRows+" rows:",cacheTime);}return cache;};function getElementText(config,node){var text="";if(!node)return"";if(!config.supportsTextContent)config.supportsTextContent=node.textContent||false;if(config.textExtraction=="simple"){if(config.supportsTextContent){text=node.textContent;}else{if(node.childNodes[0]&&node.childNodes[0].hasChildNodes()){text=node.childNodes[0].innerHTML;}else{text=node.innerHTML;}}}else{if(typeof(config.textExtraction)=="function"){text=config.textExtraction(node);}else{text=$(node).text();}}return text;}function appendToTable(table,cache){if(table.config.debug){var appendTime=new Date()}var c=cache,r=c.row,n=c.normalized,totalRows=n.length,checkCell=(n[0].length-1),tableBody=$(table.tBodies[0]),rows=[];for(var i=0;i<totalRows;i++){var pos=n[i][checkCell];rows.push(r[pos]);if(!table.config.appender){var l=r[pos].length;for(var j=0;j<l;j++){tableBody[0].appendChild(r[pos][j]);}}}if(table.config.appender){table.config.appender(table,rows);}rows=null;if(table.config.debug){benchmark("Rebuilt table:",appendTime);}applyWidget(table);setTimeout(function(){$(table).trigger("sortEnd");},0);};function buildHeaders(table){if(table.config.debug){var time=new Date();}var meta=($.metadata)?true:false;var header_index=computeTableHeaderCellIndexes(table);$tableHeaders=$(table.config.selectorHeaders,table).each(function(index){this.column=header_index[this.parentNode.rowIndex+"-"+this.cellIndex];this.order=formatSortingOrder(table.config.sortInitialOrder);this.count=this.order;if(checkHeaderMetadata(this)||checkHeaderOptions(table,index))this.sortDisabled=true;if(checkHeaderOptionsSortingLocked(table,index))this.order=this.lockedOrder=checkHeaderOptionsSortingLocked(table,index);if(!this.sortDisabled){var $th=$(this).addClass(table.config.cssHeader);if(table.config.onRenderHeader)table.config.onRenderHeader.apply($th);}table.config.headerList[index]=this;});if(table.config.debug){benchmark("Built headers:",time);log($tableHeaders);}return $tableHeaders;};function computeTableHeaderCellIndexes(t){var matrix=[];var lookup={};var thead=t.getElementsByTagName('THEAD')[0];var trs=thead.getElementsByTagName('TR');for(var i=0;i<trs.length;i++){var cells=trs[i].cells;for(var j=0;j<cells.length;j++){var c=cells[j];var rowIndex=c.parentNode.rowIndex;var cellId=rowIndex+"-"+c.cellIndex;var rowSpan=c.rowSpan||1;var colSpan=c.colSpan||1
var firstAvailCol;if(typeof(matrix[rowIndex])=="undefined"){matrix[rowIndex]=[];}for(var k=0;k<matrix[rowIndex].length+1;k++){if(typeof(matrix[rowIndex][k])=="undefined"){firstAvailCol=k;break;}}lookup[cellId]=firstAvailCol;for(var k=rowIndex;k<rowIndex+rowSpan;k++){if(typeof(matrix[k])=="undefined"){matrix[k]=[];}var matrixrow=matrix[k];for(var l=firstAvailCol;l<firstAvailCol+colSpan;l++){matrixrow[l]="x";}}}}return lookup;}function checkCellColSpan(table,rows,row){var arr=[],r=table.tHead.rows,c=r[row].cells;for(var i=0;i<c.length;i++){var cell=c[i];if(cell.colSpan>1){arr=arr.concat(checkCellColSpan(table,headerArr,row++));}else{if(table.tHead.length==1||(cell.rowSpan>1||!r[row+1])){arr.push(cell);}}}return arr;};function checkHeaderMetadata(cell){if(($.metadata)&&($(cell).metadata().sorter===false)){return true;};return false;}function checkHeaderOptions(table,i){if((table.config.headers[i])&&(table.config.headers[i].sorter===false)){return true;};return false;}function checkHeaderOptionsSortingLocked(table,i){if((table.config.headers[i])&&(table.config.headers[i].lockedOrder))return table.config.headers[i].lockedOrder;return false;}function applyWidget(table){var c=table.config.widgets;var l=c.length;for(var i=0;i<l;i++){getWidgetById(c[i]).format(table);}}function getWidgetById(name){var l=widgets.length;for(var i=0;i<l;i++){if(widgets[i].id.toLowerCase()==name.toLowerCase()){return widgets[i];}}};function formatSortingOrder(v){if(typeof(v)!="Number"){return(v.toLowerCase()=="desc")?1:0;}else{return(v==1)?1:0;}}function isValueInArray(v,a){var l=a.length;for(var i=0;i<l;i++){if(a[i][0]==v){return true;}}return false;}function setHeadersCss(table,$headers,list,css){$headers.removeClass(css[0]).removeClass(css[1]);var h=[];$headers.each(function(offset){if(!this.sortDisabled){h[this.column]=$(this);}});var l=list.length;for(var i=0;i<l;i++){h[list[i][0]].addClass(css[list[i][1]]);}}function fixColumnWidth(table,$headers){var c=table.config;if(c.widthFixed){var colgroup=$('<colgroup>');$("tr:first td",table.tBodies[0]).each(function(){colgroup.append($('<col>').css('width',$(this).width()));});$(table).prepend(colgroup);};}function updateHeaderSortCount(table,sortList){var c=table.config,l=sortList.length;for(var i=0;i<l;i++){var s=sortList[i],o=c.headerList[s[0]];o.count=s[1];o.count++;}}function multisort(table,sortList,cache){if(table.config.debug){var sortTime=new Date();}var dynamicExp="var sortWrapper = function(a,b) {",l=sortList.length;for(var i=0;i<l;i++){var c=sortList[i][0];var order=sortList[i][1];var s=(table.config.parsers[c].type=="text")?((order==0)?makeSortFunction("text","asc",c):makeSortFunction("text","desc",c)):((order==0)?makeSortFunction("numeric","asc",c):makeSortFunction("numeric","desc",c));var e="e"+i;dynamicExp+="var "+e+" = "+s;dynamicExp+="if("+e+") { return "+e+"; } ";dynamicExp+="else { ";}var orgOrderCol=cache.normalized[0].length-1;dynamicExp+="return a["+orgOrderCol+"]-b["+orgOrderCol+"];";for(var i=0;i<l;i++){dynamicExp+="}; ";}dynamicExp+="return 0; ";dynamicExp+="}; ";if(table.config.debug){benchmark("Evaling expression:"+dynamicExp,new Date());}eval(dynamicExp);cache.normalized.sort(sortWrapper);if(table.config.debug){benchmark("Sorting on "+sortList.toString()+" and dir "+order+" time:",sortTime);}return cache;};function makeSortFunction(type,direction,index){var a="a["+index+"]",b="b["+index+"]";if(type=='text'&&direction=='asc'){return"("+a+" == "+b+" ? 0 : ("+a+" === null ? Number.POSITIVE_INFINITY : ("+b+" === null ? Number.NEGATIVE_INFINITY : ("+a+" < "+b+") ? -1 : 1 )));";}else if(type=='text'&&direction=='desc'){return"("+a+" == "+b+" ? 0 : ("+a+" === null ? Number.POSITIVE_INFINITY : ("+b+" === null ? Number.NEGATIVE_INFINITY : ("+b+" < "+a+") ? -1 : 1 )));";}else if(type=='numeric'&&direction=='asc'){return"("+a+" === null && "+b+" === null) ? 0 :("+a+" === null ? Number.POSITIVE_INFINITY : ("+b+" === null ? Number.NEGATIVE_INFINITY : "+a+" - "+b+"));";}else if(type=='numeric'&&direction=='desc'){return"("+a+" === null && "+b+" === null) ? 0 :("+a+" === null ? Number.POSITIVE_INFINITY : ("+b+" === null ? Number.NEGATIVE_INFINITY : "+b+" - "+a+"));";}};function makeSortText(i){return"((a["+i+"] < b["+i+"]) ? -1 : ((a["+i+"] > b["+i+"]) ? 1 : 0));";};function makeSortTextDesc(i){return"((b["+i+"] < a["+i+"]) ? -1 : ((b["+i+"] > a["+i+"]) ? 1 : 0));";};function makeSortNumeric(i){return"a["+i+"]-b["+i+"];";};function makeSortNumericDesc(i){return"b["+i+"]-a["+i+"];";};function sortText(a,b){if(table.config.sortLocaleCompare)return a.localeCompare(b);return((a<b)?-1:((a>b)?1:0));};function sortTextDesc(a,b){if(table.config.sortLocaleCompare)return b.localeCompare(a);return((b<a)?-1:((b>a)?1:0));};function sortNumeric(a,b){return a-b;};function sortNumericDesc(a,b){return b-a;};function getCachedSortType(parsers,i){return parsers[i].type;};this.construct=function(settings){return this.each(function(){if(!this.tHead||!this.tBodies)return;var $this,$document,$headers,cache,config,shiftDown=0,sortOrder;this.config={};config=$.extend(this.config,$.tablesorter.defaults,settings);$this=$(this);$.data(this,"tablesorter",config);$headers=buildHeaders(this);this.config.parsers=buildParserCache(this,$headers);cache=buildCache(this);var sortCSS=[config.cssDesc,config.cssAsc];fixColumnWidth(this);$headers.click(function(e){var totalRows=($this[0].tBodies[0]&&$this[0].tBodies[0].rows.length)||0;if(!this.sortDisabled&&totalRows>0){$this.trigger("sortStart");var $cell=$(this);var i=this.column;this.order=this.count++%2;if(this.lockedOrder)this.order=this.lockedOrder;if(!e[config.sortMultiSortKey]){config.sortList=[];if(config.sortForce!=null){var a=config.sortForce;for(var j=0;j<a.length;j++){if(a[j][0]!=i){config.sortList.push(a[j]);}}}config.sortList.push([i,this.order]);}else{if(isValueInArray(i,config.sortList)){for(var j=0;j<config.sortList.length;j++){var s=config.sortList[j],o=config.headerList[s[0]];if(s[0]==i){o.count=s[1];o.count++;s[1]=o.count%2;}}}else{config.sortList.push([i,this.order]);}};setTimeout(function(){setHeadersCss($this[0],$headers,config.sortList,sortCSS);appendToTable($this[0],multisort($this[0],config.sortList,cache));},1);return false;}}).mousedown(function(){if(config.cancelSelection){this.onselectstart=function(){return false};return false;}});$this.bind("update",function(){var me=this;setTimeout(function(){me.config.parsers=buildParserCache(me,$headers);cache=buildCache(me);},1);}).bind("updateCell",function(e,cell){var config=this.config;var pos=[(cell.parentNode.rowIndex-1),cell.cellIndex];cache.normalized[pos[0]][pos[1]]=config.parsers[pos[1]].format(getElementText(config,cell),cell);}).bind("sorton",function(e,list){$(this).trigger("sortStart");config.sortList=list;var sortList=config.sortList;updateHeaderSortCount(this,sortList);setHeadersCss(this,$headers,sortList,sortCSS);appendToTable(this,multisort(this,sortList,cache));}).bind("appendCache",function(){appendToTable(this,cache);}).bind("applyWidgetId",function(e,id){getWidgetById(id).format(this);}).bind("applyWidgets",function(){applyWidget(this);});if($.metadata&&($(this).metadata()&&$(this).metadata().sortlist)){config.sortList=$(this).metadata().sortlist;}if(config.sortList.length>0){$this.trigger("sorton",[config.sortList]);}applyWidget(this);});};this.addParser=function(parser){var l=parsers.length,a=true;for(var i=0;i<l;i++){if(parsers[i].id.toLowerCase()==parser.id.toLowerCase()){a=false;}}if(a){parsers.push(parser);};};this.addWidget=function(widget){widgets.push(widget);};this.formatFloat=function(s){var i=parseFloat(s);return(isNaN(i))?0:i;};this.formatInt=function(s){var i=parseInt(s);return(isNaN(i))?0:i;};this.isDigit=function(s,config){return/^[-+]?\d*$/.test($.trim(s.replace(/[,.']/g,'')));};this.clearTableBody=function(table){if($.browser.msie){function empty(){while(this.firstChild)this.removeChild(this.firstChild);}empty.apply(table.tBodies[0]);}else{table.tBodies[0].innerHTML="";}};}});$.fn.extend({tablesorter:$.tablesorter.construct});var ts=$.tablesorter;ts.addParser({id:"text",is:function(s){return true;},format:function(s){return $.trim(s.toLocaleLowerCase());},type:"text"});ts.addParser({id:"digit",is:function(s,table){var c=table.config;return $.tablesorter.isDigit(s,c);},format:function(s){return $.tablesorter.formatFloat(s);},type:"numeric"});ts.addParser({id:"currency",is:function(s){return/^[Â£$â‚¬?.]/.test(s);},format:function(s){return $.tablesorter.formatFloat(s.replace(new RegExp(/[Â£$â‚¬]/g),""));},type:"numeric"});ts.addParser({id:"ipAddress",is:function(s){return/^\d{2,3}[\.]\d{2,3}[\.]\d{2,3}[\.]\d{2,3}$/.test(s);},format:function(s){var a=s.split("."),r="",l=a.length;for(var i=0;i<l;i++){var item=a[i];if(item.length==2){r+="0"+item;}else{r+=item;}}return $.tablesorter.formatFloat(r);},type:"numeric"});ts.addParser({id:"url",is:function(s){return/^(https?|ftp|file):\/\/$/.test(s);},format:function(s){return jQuery.trim(s.replace(new RegExp(/(https?|ftp|file):\/\//),''));},type:"text"});ts.addParser({id:"isoDate",is:function(s){return/^\d{4}[\/-]\d{1,2}[\/-]\d{1,2}$/.test(s);},format:function(s){return $.tablesorter.formatFloat((s!="")?new Date(s.replace(new RegExp(/-/g),"/")).getTime():"0");},type:"numeric"});ts.addParser({id:"percent",is:function(s){return/\%$/.test($.trim(s));},format:function(s){return $.tablesorter.formatFloat(s.replace(new RegExp(/%/g),""));},type:"numeric"});ts.addParser({id:"usLongDate",is:function(s){return s.match(new RegExp(/^[A-Za-z]{3,10}\.? [0-9]{1,2}, ([0-9]{4}|'?[0-9]{2}) (([0-2]?[0-9]:[0-5][0-9])|([0-1]?[0-9]:[0-5][0-9]\s(AM|PM)))$/));},format:function(s){return $.tablesorter.formatFloat(new Date(s).getTime());},type:"numeric"});ts.addParser({id:"shortDate",is:function(s){return/\d{1,2}[\/\-]\d{1,2}[\/\-]\d{2,4}/.test(s);},format:function(s,table){var c=table.config;s=s.replace(/\-/g,"/");if(c.dateFormat=="us"){s=s.replace(/(\d{1,2})[\/\-](\d{1,2})[\/\-](\d{4})/,"$3/$1/$2");}else if(c.dateFormat=="uk"){s=s.replace(/(\d{1,2})[\/\-](\d{1,2})[\/\-](\d{4})/,"$3/$2/$1");}else if(c.dateFormat=="dd/mm/yy"||c.dateFormat=="dd-mm-yy"){s=s.replace(/(\d{1,2})[\/\-](\d{1,2})[\/\-](\d{2})/,"$1/$2/$3");}return $.tablesorter.formatFloat(new Date(s).getTime());},type:"numeric"});ts.addParser({id:"time",is:function(s){return/^(([0-2]?[0-9]:[0-5][0-9])|([0-1]?[0-9]:[0-5][0-9]\s(am|pm)))$/.test(s);},format:function(s){return $.tablesorter.formatFloat(new Date("2000/01/01 "+s).getTime());},type:"numeric"});ts.addParser({id:"metadata",is:function(s){return false;},format:function(s,table,cell){var c=table.config,p=(!c.parserMetadataName)?'sortValue':c.parserMetadataName;return $(cell).metadata()[p];},type:"numeric"});ts.addWidget({id:"zebra",format:function(table){if(table.config.debug){var time=new Date();}var $tr,row=-1,odd;$("tr:visible",table.tBodies[0]).each(function(i){$tr=$(this);if(!$tr.hasClass(table.config.cssChildRow))row++;odd=(row%2==0);$tr.removeClass(table.config.widgetZebra.css[odd?0:1]).addClass(table.config.widgetZebra.css[odd?1:0])});if(table.config.debug){$.tablesorter.benchmark("Applying Zebra widget",time);}}});})(jQuery);
/*
 * jQuery Text Overflow v0.7
 *
 * Licensed under the new BSD License.
 * Copyright 2009-2010, Bram Stein
 * All rights reserved.
 */
(function(c){var b=document.documentElement.style,d=("textOverflow" in b||"OTextOverflow" in b),a=function(f,i){var h=0,e=[],g=function(j){var l=0,k;if(h>i){return}for(l=0;l<j.length;l+=1){if(j[l].nodeType===1){k=j[l].cloneNode(false);e[e.length-1].appendChild(k);e.push(k);g(j[l].childNodes);e.pop()}else{if(j[l].nodeType===3){if(h+j[l].length<i){e[e.length-1].appendChild(j[l].cloneNode(false))}else{k=j[l].cloneNode(false);k.textContent=c.trim(k.textContent.substring(0,i-h));e[e.length-1].appendChild(k)}h+=j[l].length}else{e.appendChild(j[l].cloneNode(false))}}}};e.push(f.cloneNode(false));g(f.childNodes);return c(e.pop().childNodes)};c.extend(c.fn,{textOverflow:function(g,e){var f=g||"&#x2026;";if(!d){return this.each(function(){var l=c(this),m=l.clone(),p=l.clone(),k=l.text(),h=l.width(),n=0,o=0,j=k.length,i=function(){if(h!==l.width()){l.replaceWith(p);l=p;p=l.clone();l.textOverflow(g,false);h=l.width()}};l.after(m.hide().css({position:"absolute",width:"auto",overflow:"visible","max-width":"inherit"}));if(m.width()>h){while(n<j){o=Math.floor(n+((j-n)/2));m.empty().append(a(p.get(0),o)).append(f);if(m.width()<h){n=o+1}else{j=o}}if(n<k.length){l.empty().append(a(p.get(0),n-1)).append(f)}}m.remove();if(e){setInterval(i,200)}})}else{return this}}})})(jQuery);
 /*
 * jQuery UI selectmenu
 *
 * Copyright (c) 2009 AUTHORS.txt (http://jqueryui.com/about)
 * Dual licensed under the MIT (MIT-LICENSE.txt)
 * and GPL (GPL-LICENSE.txt) licenses.
 *
 * http://docs.jquery.com/UI
 * https://github.com/fnagel/jquery-ui/wiki/Selectmenu
 */

(function($) {

$.widget("ui.selectmenu", {
	getter: "value",
	version: "1.8",
	eventPrefix: "selectmenu",
	options: {
		transferClasses: true,
		typeAhead: "sequential",
		style: 'dropdown',
		positionOptions: {
			my: "left top",
			at: "left bottom",
			offset: null
		},
		width: null, 
		menuWidth: null, 
		handleWidth: 26,
		maxHeight: null,
		icons: null, 
		format: null,
		bgImage: function() {},
		wrapperElement: ""
	},

	_create: function() {
		var self = this, o = this.options;

		// set a default id value, generate a new random one if not set by developer
		var selectmenuId = this.element.attr('id') || 'ui-selectmenu-' + Math.random().toString(16).slice(2, 10);

		// quick array of button and menu id's
		this.ids = [ selectmenuId + '-button', selectmenuId + '-menu' ];

		// define safe mouseup for future toggling
		this._safemouseup = true;
		
		// FIXME temp workaround for IE
		if ($.browser.msie) o.typeAhead = "";

		// create menu button wrapper
		this.newelement = $('<a class="' + this.widgetBaseClass + ' ui-widget ui-state-default ui-corner-all" id="' + this.ids[0] + '" role="button" href="#" tabindex="0" aria-haspopup="true" aria-owns="' + this.ids[1] + '"></a>')
			.insertAfter(this.element);
		this.newelement.wrap(o.wrapperElement);

		// transfer tabindex
		var tabindex = this.element.attr('tabindex');
		if (tabindex) {
			this.newelement.attr('tabindex', tabindex);
		}

		// save reference to select in data for ease in calling methods
		this.newelement.data('selectelement', this.element);
		
		// menu icon
		this.selectmenuIcon = $('<span class="' + this.widgetBaseClass + '-icon ui-icon"></span>')
			.prependTo(this.newelement);
			
		// append status span to button
		this.newelement.prepend('<span class="' + self.widgetBaseClass + '-status" />');
			
		// make associated form label trigger focus
		$('label[for="' + this.element.attr('id') + '"]')
			.attr('for', this.ids[0])
			.bind('click.selectmenu', function() {
				self.newelement[0].focus();
				return false;
			});	
			
		// click toggle for menu visibility
		this.newelement
			.bind('mousedown.selectmenu', function(event) {
				self._toggle(event, true);
				// make sure a click won't open/close instantly
				if (o.style == "popup") {
					self._safemouseup = false;
					setTimeout(function() { self._safemouseup = true; }, 300);
				}
				return false;
			})
			.bind('click.selectmenu', function() {
				return false;
			})
			.bind("keydown.selectmenu", function(event) {
				var ret = false;
				switch (event.keyCode) {
					case $.ui.keyCode.ENTER:
						ret = true;
						break;
					case $.ui.keyCode.SPACE:
						self._toggle(event);	
						break;
					case $.ui.keyCode.UP:
						if (event.altKey) {
							self.open(event);
						} else {
							self._moveSelection(-1);
						}
						break;
					case $.ui.keyCode.DOWN:
						if (event.altKey) {
							self.open(event);
						} else {
							self._moveSelection(1);
						}
						break;
					case $.ui.keyCode.LEFT:
						self._moveSelection(-1);
						break;
					case $.ui.keyCode.RIGHT:
						self._moveSelection(1);
						break;
					case $.ui.keyCode.TAB:
						ret = true;
						break;
					default:
						ret = true;
						self._typeAhead(event.keyCode, 'mouseup');
						break;	
				}
				return ret;
			})
			.bind('mouseover.selectmenu focus.selectmenu', function() { 
				if (!o.disabled) {
					$(this).addClass(self.widgetBaseClass + '-focus ui-state-hover');
				}
			})
			.bind('mouseout.selectmenu blur.selectmenu', function() {
				if (!o.disabled) {
					$(this).removeClass(self.widgetBaseClass + '-focus ui-state-hover');
				}
			});

		// document click closes menu
		$(document).bind("mousedown.selectmenu", function(event) {
			self.close(event);
		});

		// change event on original selectmenu
		this.element
			.bind("click.selectmenu", function() {
				self._refreshValue();
			})
			// FIXME: newelement can be null under unclear circumstances in IE8 
			// TODO not sure if this is still a problem (fnagel 20.03.11)
			.bind("focus.selectmenu", function() {
				if (self.newelement) {
					self.newelement[0].focus();
				}
			});

		// original selectmenu width
		var selectWidth = this.element.width();

		// set menu button width
		this.newelement.width(o.width ? o.width : selectWidth);

		// hide original selectmenu element
		this.element.hide();		

		// create menu portion, append to body
		this.list = $('<ul class="' + self.widgetBaseClass + '-menu ui-widget ui-widget-content" aria-hidden="true" role="listbox" aria-labelledby="' + this.ids[0] + '" id="' + this.ids[1] + '"></ul>').appendTo('body');
		this.list.wrap(o.wrapperElement);				

		// transfer menu click to menu button
		this.list
			.bind("keydown.selectmenu", function(event) {
				var ret = false;
				switch (event.keyCode) {
					case $.ui.keyCode.UP:
						if (event.altKey) {
							self.close(event, true);
						} else {
							self._moveFocus(-1);
						}
						break;
					case $.ui.keyCode.DOWN:
						if (event.altKey) {
							self.close(event, true);
						} else {
							self._moveFocus(1);
						}
						break;	
					case $.ui.keyCode.LEFT:
						self._moveFocus(-1);
						break;
					case $.ui.keyCode.RIGHT:
						self._moveFocus(1);
						break;	
					case $.ui.keyCode.HOME:
						self._moveFocus(':first');
						break;		
					case $.ui.keyCode.PAGE_UP:
						self._scrollPage('up');
						break;	
					case $.ui.keyCode.PAGE_DOWN:
						self._scrollPage('down');
						break;
					case $.ui.keyCode.END:
						self._moveFocus(':last');
						break;		
					case $.ui.keyCode.ENTER:
					case $.ui.keyCode.SPACE:
						self.close(event, true);
						$(event.target).parents('li:eq(0)').trigger('mouseup');
						break;		
					case $.ui.keyCode.TAB:
						ret = true;
						self.close(event, true);
						$(event.target).parents('li:eq(0)').trigger('mouseup');
						break;	
					case $.ui.keyCode.ESCAPE:
						self.close(event, true);
						break;
					default:
						ret = true;	
						self._typeAhead(event.keyCode,'focus');					
						break;	
				}
				return ret;
			});			
		
		// needed when window is resized
		$(window).bind( "resize.selectmenu", $.proxy( self._refreshPosition, this ) );
	},

	_init: function() {
		var self = this, o = this.options;
		
		// serialize selectmenu element options	
		var selectOptionData = [];
		this.element
			.find('option')
			.each(function() {
				selectOptionData.push({
					value: $(this).attr('value'),
					text: self._formatText($(this).text()),
					selected: $(this).attr('selected'),
					disabled: $(this).attr('disabled'),
					classes: $(this).attr('class'),
					typeahead: $(this).attr('typeahead'),
					parentOptGroup: $(this).parent('optgroup'),
					bgImage: o.bgImage.call($(this))
				});
			});		
				
		// active state class is only used in popup style
		var activeClass = (self.options.style == "popup") ? " ui-state-active" : "";

		// empty list so we can refresh the selectmenu via selectmenu()
		this.list.html("");

		// write li's
		for (var i = 0; i < selectOptionData.length; i++) {
				var thisLi = $('<li role="presentation"' + (selectOptionData[i].disabled ? ' class="' + this.namespace + '-state-disabled' + '"' : '' ) + '><a href="#" tabindex="-1" role="option"' + (selectOptionData[i].disabled ? ' aria-disabled="true"' : '' ) + ' aria-selected="false"' + (selectOptionData[i].typeahead ? ' typeahead="' + selectOptionData[i].typeahead + '"' : '' ) + '>'+ selectOptionData[i].text +'</a></li>')
				.data('index', i)
				.addClass(selectOptionData[i].classes)
				.data('optionClasses', selectOptionData[i].classes || '')
				.bind("mouseup.selectmenu", function(event) {
					if (self._safemouseup && !self._disabled(event.currentTarget) && !self._disabled($( event.currentTarget ).parents( "ul>li." + self.widgetBaseClass + "-group " )) ) {
						var changed = $(this).data('index') != self._selectedIndex();
						self.index($(this).data('index'));
						self.select(event);
						if (changed) {
							self.change(event);
						}
						self.close(event, true);
					}
					return false;
				})
				.bind("click.selectmenu", function() {
					return false;
				})
				.bind('mouseover.selectmenu focus.selectmenu', function(e) {
					// no hover if diabled
					if (!$(e.currentTarget).hasClass(self.namespace + '-state-disabled')) {
						self._selectedOptionLi().addClass(activeClass); 
						self._focusedOptionLi().removeClass(self.widgetBaseClass + '-item-focus ui-state-hover'); 
						$(this).removeClass('ui-state-active').addClass(self.widgetBaseClass + '-item-focus ui-state-hover'); 
					}
				})
				.bind('mouseout.selectmenu blur.selectmenu', function() { 
					if ($(this).is(self._selectedOptionLi().selector)) {
						$(this).addClass(activeClass);
					}
					$(this).removeClass(self.widgetBaseClass + '-item-focus ui-state-hover');
				});

			// optgroup or not...
			if ( selectOptionData[i].parentOptGroup.length ) {
				var optGroupName = self.widgetBaseClass + '-group-' + this.element.find( 'optgroup' ).index( selectOptionData[i].parentOptGroup );
				if (this.list.find( 'li.' + optGroupName ).length ) {
					this.list.find( 'li.' + optGroupName + ':last ul' ).append( thisLi );
				} else {
					$(' <li role="presentation" class="' + self.widgetBaseClass + '-group ' + optGroupName + (selectOptionData[i].parentOptGroup.attr("disabled") ? ' ' + this.namespace + '-state-disabled" aria-disabled="true"' : '"' ) + '><span class="' + self.widgetBaseClass + '-group-label">' + selectOptionData[i].parentOptGroup.attr('label') + '</span><ul></ul></li> ')
						.appendTo( this.list )
						.find( 'ul' )
						.append( thisLi );
				}
			} else {
				thisLi.appendTo(this.list);
			}
			
			// this allows for using the scrollbar in an overflowed list
			this.list.bind('mousedown.selectmenu mouseup.selectmenu', function() { return false; });
			
			// append icon if option is specified
			if (o.icons) {
				for (var j in o.icons) {
					if (thisLi.is(o.icons[j].find)) {
						thisLi
							.data('optionClasses', selectOptionData[i].classes + ' ' + self.widgetBaseClass + '-hasIcon')
							.addClass(self.widgetBaseClass + '-hasIcon');
						var iconClass = o.icons[j].icon || "";						
						thisLi
							.find('a:eq(0)')
							.prepend('<span class="' + self.widgetBaseClass + '-item-icon ui-icon ' + iconClass + '"></span>');
						if (selectOptionData[i].bgImage) {
							thisLi.find('span').css('background-image', selectOptionData[i].bgImage);
						}
					}
				}
			}
		}	
				
		// we need to set and unset the CSS classes for dropdown and popup style
		var isDropDown = (o.style == 'dropdown');
		this.newelement
			.toggleClass(self.widgetBaseClass + "-dropdown", isDropDown)
			.toggleClass(self.widgetBaseClass + "-popup", !isDropDown);
		this.list
			.toggleClass(self.widgetBaseClass + "-menu-dropdown ui-corner-bottom", isDropDown)
			.toggleClass(self.widgetBaseClass + "-menu-popup ui-corner-all", !isDropDown)
			// add corners to top and bottom menu items
			.find('li:first')
			.toggleClass("ui-corner-top", !isDropDown)
			.end().find('li:last')
			.addClass("ui-corner-bottom");
		this.selectmenuIcon
			.toggleClass('ui-icon-triangle-1-s', isDropDown)
			.toggleClass('ui-icon-triangle-2-n-s', !isDropDown);

		// transfer classes to selectmenu and list
		if (o.transferClasses) {
			var transferClasses = this.element.attr('class') || '';
			this.newelement.add(this.list).addClass(transferClasses);
		}

		// original selectmenu width
		var selectWidth = this.element.width();

		// set menu width to either menuWidth option value, width option value, or select width 
		if (o.style == 'dropdown') { 
			this.list.width(o.menuWidth ? o.menuWidth : (o.width ? o.width : selectWidth)); 
		} else { 
			this.list.width(o.menuWidth ? o.menuWidth : (o.width ? o.width - o.handleWidth : selectWidth - o.handleWidth)); 
		}

		// calculate default max height
		if (o.maxHeight) {
			// set max height from option 
			if (o.maxHeight < this.list.height()) {
				this.list.height(o.maxHeight);
			}
		} else {
			if (!o.format && ($(window).height() / 3) < this.list.height()) {
				o.maxHeight = $(window).height() / 3;
				this.list.height(o.maxHeight);
			}
		}

		// save reference to actionable li's (not group label li's)
		this._optionLis = this.list.find('li:not(.' + self.widgetBaseClass + '-group)');
						
		// transfer disabled state
		if (this.element.attr('disabled') === true) {
			this.disable();
		}

		// update value
		this.index(this._selectedIndex());		

		// needed when selectmenu is placed at the very bottom / top of the page
		window.setTimeout(function() {
			self._refreshPosition();
		}, 200);
	},

	destroy: function() {
		this.element.removeData( this.widgetName )
			.removeClass( this.widgetBaseClass + '-disabled' + ' ' + this.namespace + '-state-disabled' )
			.removeAttr( 'aria-disabled' )
			.unbind( ".selectmenu" );
			
		$( window ).unbind( ".selectmenu" );
		$( document ).unbind( ".selectmenu" );
	
		// unbind click on label, reset its for attr
		$( 'label[for=' + this.newelement.attr('id') + ']' )
			.attr( 'for', this.element.attr( 'id' ) )
			.unbind( '.selectmenu' );
		
		if ( this.options.wrapperElement ) {
			this.newelement.find( this.options.wrapperElement ).remove();
			this.list.find( this.options.wrapperElement ).remove();
		} else {
			this.newelement.remove();
			this.list.remove();
		}
		this.element.show();	

		// call widget destroy function
		$.Widget.prototype.destroy.apply(this, arguments);
	},

	_typeAhead: function(code, eventType){
		var self = this, focusFound = false, C = String.fromCharCode(code);
		c = C.toLowerCase();

		if (self.options.typeAhead == 'sequential') {
			// clear the timeout so we can use _prevChar
			window.clearTimeout('ui.selectmenu-' + self.selectmenuId);

			// define our find var
			var find = typeof(self._prevChar) == 'undefined' ? '' : self._prevChar.join('');
			
			function focusOptSeq(elem, ind, c){
				focusFound = true;
				$(elem).trigger(eventType);
				typeof(self._prevChar) == 'undefined' ? self._prevChar = [c] : self._prevChar[self._prevChar.length] = c;
			}
			this.list.find('li a').each(function(i) {	
				if (!focusFound) {
					// allow the typeahead attribute on the option tag for a more specific lookup
					var thisText = $(this).attr('typeahead') || $(this).text();
					if (thisText.indexOf(find+C) == 0) {
						focusOptSeq(this,i, C)
					} else if (thisText.indexOf(find+c) == 0) {
						focusOptSeq(this,i,c)
					}
				}
			});
			
			// if we didnt find it clear the prevChar
			// if (!focusFound) {
				//self._prevChar = undefined
			// }

			// set a 1 second timeout for sequenctial typeahead
			//  	keep this set even if we have no matches so it doesnt typeahead somewhere else
			window.setTimeout(function(el) {
				el._prevChar = undefined;
			}, 1000, self);

		} else {
			//define self._prevChar if needed
			if (!self._prevChar){ self._prevChar = ['',0]; }

			var focusFound = false;
			function focusOpt(elem, ind){
				focusFound = true;
				$(elem).trigger(eventType);
				self._prevChar[1] = ind;
			}
			this.list.find('li a').each(function(i){	
				if(!focusFound){
					var thisText = $(this).text();
					if( thisText.indexOf(C) == 0 || thisText.indexOf(c) == 0){
							if(self._prevChar[0] == C){
								if(self._prevChar[1] < i){ focusOpt(this,i); }	
							}
							else{ focusOpt(this,i); }	
					}
				}
			});
			this._prevChar[0] = C;
		}
	},
	
	// returns some usefull information, called by callbacks only
	_uiHash: function() {
		var index = this.index();
		return {
			index: index,
			option: $("option", this.element).get(index),
			value: this.element[0].value
		};
	},

	open: function(event) {
		var self = this;
		if ( this.newelement.attr("aria-disabled") != 'true' ) {
			// TODO: seems to be useless
			// this._refreshPosition();
			this._closeOthers(event);
			this.newelement
				.addClass('ui-state-active');
			if (self.options.wrapperElement) {
				this.list.parent().appendTo('body');
			} else {
				this.list.appendTo('body');
			}
			
			this.list.addClass(self.widgetBaseClass + '-open').attr('aria-hidden', false);
			// FIX IE: Refreshing position before focusing the element, prevents IE from scrolling to the focused element before it is in position.
			this._refreshPosition();
			this.list.find('li:not(.' + self.widgetBaseClass + '-group):eq(' + this._selectedIndex() + ') a')[0].focus();
			if ( this.options.style == "dropdown" ) {
				this.newelement.removeClass('ui-corner-all').addClass('ui-corner-top');
			}
			this._trigger("open", event, this._uiHash());
		}
	},

	close: function(event, retainFocus) {
		if ( this.newelement.is('.ui-state-active') ) {
			this.newelement
				.removeClass('ui-state-active');
			this.list
				.attr('aria-hidden', true)
				.removeClass(this.widgetBaseClass + '-open');
			if ( this.options.style == "dropdown" ) {
				this.newelement.removeClass('ui-corner-top').addClass('ui-corner-all');
			}
			if ( retainFocus ) {
				this.newelement.focus();
			}
			this._trigger("close", event, this._uiHash());
		}
	},

	change: function(event) {
		this.element.trigger("change");
		this._trigger("change", event, this._uiHash());
	},

	select: function(event) {
		this._trigger("select", event, this._uiHash());
	},

	_closeOthers: function(event) {
		$('.' + this.widgetBaseClass + '.ui-state-active').not(this.newelement).each(function() {
			$(this).data('selectelement').selectmenu('close', event);
		});
		$('.' + this.widgetBaseClass + '.ui-state-hover').trigger('mouseout');
	},

	_toggle: function(event, retainFocus) {
		if ( this.list.is('.' + this.widgetBaseClass + '-open') ) {
			this.close(event, retainFocus);
		} else {
			this.open(event);
		}
	},

	_formatText: function(text) {
		return (this.options.format ? this.options.format(text) : text);
	},

	_selectedIndex: function() {
		return this.element[0].selectedIndex;
	},

	_selectedOptionLi: function() {
		return this._optionLis.eq(this._selectedIndex());
	},

	_focusedOptionLi: function() {
		return this.list.find('.' + this.widgetBaseClass + '-item-focus');
	},

	_moveSelection: function(amt) {
		var currIndex = parseInt(this._selectedOptionLi().data('index'), 10);
		var newIndex = currIndex + amt;
		// do not loop when using up key
		if (newIndex >= 0 )  return this._optionLis.eq(newIndex).trigger('mouseup');
	},

	_moveFocus: function(amt) {
		if (!isNaN(amt)) {
			var currIndex = parseInt(this._focusedOptionLi().data('index') || 0, 10);
			var newIndex = currIndex + amt;
		}
		else {
			var newIndex = parseInt(this._optionLis.filter(amt).data('index'), 10);
		}

		if (newIndex < 0) {
			newIndex = 0;
		}
		if (newIndex > this._optionLis.size() - 1) {
			newIndex = this._optionLis.size() - 1;
		}
		
		var activeID = this.widgetBaseClass + '-item-' + Math.round(Math.random() * 1000);

		this._focusedOptionLi().find('a:eq(0)').attr('id', '');
		
		if (this._optionLis.eq(newIndex).hasClass( this.namespace + '-state-disabled' )) {
			// if option at newIndex is disabled, call _moveFocus, incrementing amt by one
			(amt > 0) ? amt++ : amt--;
			this._moveFocus(amt, newIndex);
		} else {
			this._optionLis.eq(newIndex).find('a:eq(0)').attr('id',activeID).focus();
		}
		
		this.list.attr('aria-activedescendant', activeID);
	},

	_scrollPage: function(direction) {
		var numPerPage = Math.floor(this.list.outerHeight() / this.list.find('li:first').outerHeight());
		numPerPage = (direction == 'up' ? -numPerPage : numPerPage);
		this._moveFocus(numPerPage);
	},

	_setOption: function(key, value) {
		this.options[key] = value;
		// set 
		if (key == 'disabled') {
			this.close();
			this.element
				.add(this.newelement)
				.add(this.list)[value ? 'addClass' : 'removeClass'](
					this.widgetBaseClass + '-disabled' + ' ' +
					this.namespace + '-state-disabled')
				.attr("aria-disabled", value);
		}
	},

	disable: function(index, type){
			// if options is not provided, call the parents disable function
			if ( typeof( index ) == 'undefined' ) {
				this._setOption( 'disabled', true );
			} else {
				if ( type == "optgroup" ) {
					this._disableOptgroup(index);
				} else {
					this._disableOption(index);
				}
			}
	},

	enable: function(index, type) {
			// if options is not provided, call the parents enable function
			if ( typeof( index ) == 'undefined' ) {
				this._setOption('disabled', false);
			} else {
				if ( type == "optgroup" ) {
					this._enableOptgroup(index);
				} else {
					this._enableOption(index);
				}
			}
	},

	_disabled: function(elem) {
			return $(elem).hasClass( this.namespace + '-state-disabled' );
	},
	

	_disableOption: function(index) {
			var optionElem = this._optionLis.eq(index);
			if (optionElem) {
				optionElem.addClass(this.namespace + '-state-disabled')
					.find("a").attr("aria-disabled", true);
				this.element.find("option").eq(index).attr("disabled", "disabled");
			}
	},

	_enableOption: function(index) {
			var optionElem = this._optionLis.eq(index);
			if (optionElem) {
				optionElem.removeClass( this.namespace + '-state-disabled' )
					.find("a").attr("aria-disabled", false);
				this.element.find("option").eq(index).removeAttr("disabled");
			}
	},

	_disableOptgroup: function(index) {		
			var optGroupElem = this.list.find( 'li.' + this.widgetBaseClass + '-group-' + index );
			if (optGroupElem) {
				optGroupElem.addClass(this.namespace + '-state-disabled')
					.attr("aria-disabled", true);
				this.element.find("optgroup").eq(index).attr("disabled", "disabled");
			}
	},

	_enableOptgroup: function(index) {		
			var optGroupElem = this.list.find( 'li.' + this.widgetBaseClass + '-group-' + index );
			if (optGroupElem) {
				optGroupElem.removeClass(this.namespace + '-state-disabled')
					.attr("aria-disabled", false);
				this.element.find("optgroup").eq(index).removeAttr("disabled");
			}
	},
	
	index: function(newValue) {
		if (arguments.length) {
			if (!this._disabled($(this._optionLis[newValue]))) {
				this.element[0].selectedIndex = newValue;
				this._refreshValue();
			} else {
				return false;
			}
		} else {
			return this._selectedIndex();
		}
	},

	value: function(newValue) {
		if (arguments.length) {
			this.element[0].value = newValue;
			this._refreshValue();
		} else {
			return this.element[0].value;
		}
	},

	_refreshValue: function() {
		var activeClass = (this.options.style == "popup") ? " ui-state-active" : "";
		var activeID = this.widgetBaseClass + '-item-' + Math.round(Math.random() * 1000);
		// deselect previous
		this.list
			.find('.' + this.widgetBaseClass + '-item-selected')
			.removeClass(this.widgetBaseClass + "-item-selected" + activeClass)
			.find('a')
			.attr('aria-selected', 'false')
			.attr('id', '');
		// select new
		this._selectedOptionLi()
			.addClass(this.widgetBaseClass + "-item-selected" + activeClass)
			.find('a')
			.attr('aria-selected', 'true')
			.attr('id', activeID);
			
		// toggle any class brought in from option
		var currentOptionClasses = (this.newelement.data('optionClasses') ? this.newelement.data('optionClasses') : "");
		var newOptionClasses = (this._selectedOptionLi().data('optionClasses') ? this._selectedOptionLi().data('optionClasses') : "");
		this.newelement
			.removeClass(currentOptionClasses)
			.data('optionClasses', newOptionClasses)
			.addClass( newOptionClasses )
			.find('.' + this.widgetBaseClass + '-status')
			.html( 
				this._selectedOptionLi()
					.find('a:eq(0)')
					.html()
			);

		this.list.attr('aria-activedescendant', activeID);
	},

	_refreshPosition: function() {
		var o = this.options;
		// if its a native pop-up we need to calculate the position of the selected li
		if (o.style == "popup" && !o.positionOptions.offset) {
			var selected = this._selectedOptionLi();
			var _offset = "0 -" + (selected.outerHeight() + selected.offset().top - this.list.offset().top);
		}
		this.list
			.css({
				zIndex: this.element.zIndex()
			})
			.position({
				// set options for position plugin
				of: o.positionOptions.of || this.newelement,
				my: o.positionOptions.my,
				at: o.positionOptions.at,
				offset: o.positionOptions.offset || _offset
			});
	}
});

})(jQuery);
/*
 * jQuery validation plug-in 1.7
 *
 * http://bassistance.de/jquery-plugins/jquery-plugin-validation/
 * http://docs.jquery.com/Plugins/Validation
 *
 * Copyright (c) 2006 - 2008 Jörn Zaefferer
 *
 * $Id: jquery.validate.js 6403 2009-06-17 14:27:16Z joern.zaefferer $
 *
 * Dual licensed under the MIT and GPL licenses:
 *   http://www.opensource.org/licenses/mit-license.php
 *   http://www.gnu.org/licenses/gpl.html
 */
(function($){$.extend($.fn,{validate:function(options){if(!this.length){options&&options.debug&&window.console&&console.warn("nothing selected, can't validate, returning nothing");return;}var validator=$.data(this[0],'validator');if(validator){return validator;}validator=new $.validator(options,this[0]);$.data(this[0],'validator',validator);if(validator.settings.onsubmit){this.find("input, button").filter(".cancel").click(function(){validator.cancelSubmit=true;});if(validator.settings.submitHandler){this.find("input, button").filter(":submit").click(function(){validator.submitButton=this;});}this.submit(function(event){if(validator.settings.debug)event.preventDefault();function handle(){if(validator.settings.submitHandler){if(validator.submitButton){var hidden=$("<input type='hidden'/>").attr("name",validator.submitButton.name).val(validator.submitButton.value).appendTo(validator.currentForm);}validator.settings.submitHandler.call(validator,validator.currentForm);if(validator.submitButton){hidden.remove();}return false;}return true;}if(validator.cancelSubmit){validator.cancelSubmit=false;return handle();}if(validator.form()){if(validator.pendingRequest){validator.formSubmitted=true;return false;}return handle();}else{validator.focusInvalid();return false;}});}return validator;},valid:function(){if($(this[0]).is('form')){return this.validate().form();}else{var valid=true;var validator=$(this[0].form).validate();this.each(function(){valid&=validator.element(this);});return valid;}},removeAttrs:function(attributes){var result={},$element=this;$.each(attributes.split(/\s/),function(index,value){result[value]=$element.attr(value);$element.removeAttr(value);});return result;},rules:function(command,argument){var element=this[0];if(command){var settings=$.data(element.form,'validator').settings;var staticRules=settings.rules;var existingRules=$.validator.staticRules(element);switch(command){case"add":$.extend(existingRules,$.validator.normalizeRule(argument));staticRules[element.name]=existingRules;if(argument.messages)settings.messages[element.name]=$.extend(settings.messages[element.name],argument.messages);break;case"remove":if(!argument){delete staticRules[element.name];return existingRules;}var filtered={};$.each(argument.split(/\s/),function(index,method){filtered[method]=existingRules[method];delete existingRules[method];});return filtered;}}var data=$.validator.normalizeRules($.extend({},$.validator.metadataRules(element),$.validator.classRules(element),$.validator.attributeRules(element),$.validator.staticRules(element)),element);if(data.required){var param=data.required;delete data.required;data=$.extend({required:param},data);}return data;}});$.extend($.expr[":"],{blank:function(a){return!$.trim(""+a.value);},filled:function(a){return!!$.trim(""+a.value);},unchecked:function(a){return!a.checked;}});$.validator=function(options,form){this.settings=$.extend(true,{},$.validator.defaults,options);this.currentForm=form;this.init();};$.validator.format=function(source,params){if(arguments.length==1)return function(){var args=$.makeArray(arguments);args.unshift(source);return $.validator.format.apply(this,args);};if(arguments.length>2&&params.constructor!=Array){params=$.makeArray(arguments).slice(1);}if(params.constructor!=Array){params=[params];}$.each(params,function(i,n){source=source.replace(new RegExp("\\{"+i+"\\}","g"),n);});return source;};$.extend($.validator,{defaults:{messages:{},groups:{},rules:{},errorClass:"error",validClass:"valid",errorElement:"label",focusInvalid:true,errorContainer:$([]),errorLabelContainer:$([]),onsubmit:true,ignore:[],ignoreTitle:false,onfocusin:function(element){this.lastActive=element;if(this.settings.focusCleanup&&!this.blockFocusCleanup){this.settings.unhighlight&&this.settings.unhighlight.call(this,element,this.settings.errorClass,this.settings.validClass);this.errorsFor(element).hide();}},onfocusout:function(element){if(!this.checkable(element)&&(element.name in this.submitted||!this.optional(element))){this.element(element);}},onkeyup:function(element){if(element.name in this.submitted||element==this.lastElement){this.element(element);}},onclick:function(element){if(element.name in this.submitted)this.element(element);else if(element.parentNode.name in this.submitted)this.element(element.parentNode);},highlight:function(element,errorClass,validClass){$(element).addClass(errorClass).removeClass(validClass);},unhighlight:function(element,errorClass,validClass){$(element).removeClass(errorClass).addClass(validClass);}},setDefaults:function(settings){$.extend($.validator.defaults,settings);},messages:{required:"This field is required.",remote:"Please fix this field.",email:"Please enter a valid email address.",url:"Please enter a valid URL.",date:"Please enter a valid date.",dateISO:"Please enter a valid date (ISO).",number:"Please enter a valid number.",digits:"Please enter only digits.",creditcard:"Please enter a valid credit card number.",equalTo:"Please enter the same value again.",accept:"Please enter a value with a valid extension.",maxlength:$.validator.format("Please enter no more than {0} characters."),minlength:$.validator.format("Please enter at least {0} characters."),rangelength:$.validator.format("Please enter a value between {0} and {1} characters long."),range:$.validator.format("Please enter a value between {0} and {1}."),max:$.validator.format("Please enter a value less than or equal to {0}."),min:$.validator.format("Please enter a value greater than or equal to {0}.")},autoCreateRanges:false,prototype:{init:function(){this.labelContainer=$(this.settings.errorLabelContainer);this.errorContext=this.labelContainer.length&&this.labelContainer||$(this.currentForm);this.containers=$(this.settings.errorContainer).add(this.settings.errorLabelContainer);this.submitted={};this.valueCache={};this.pendingRequest=0;this.pending={};this.invalid={};this.reset();var groups=(this.groups={});$.each(this.settings.groups,function(key,value){$.each(value.split(/\s/),function(index,name){groups[name]=key;});});var rules=this.settings.rules;$.each(rules,function(key,value){rules[key]=$.validator.normalizeRule(value);});function delegate(event){var validator=$.data(this[0].form,"validator"),eventType="on"+event.type.replace(/^validate/,"");validator.settings[eventType]&&validator.settings[eventType].call(validator,this[0]);}$(this.currentForm).validateDelegate(":text, :password, :file, select, textarea","focusin focusout keyup",delegate).validateDelegate(":radio, :checkbox, select, option","click",delegate);if(this.settings.invalidHandler)$(this.currentForm).bind("invalid-form.validate",this.settings.invalidHandler);},form:function(){this.checkForm();$.extend(this.submitted,this.errorMap);this.invalid=$.extend({},this.errorMap);if(!this.valid())$(this.currentForm).triggerHandler("invalid-form",[this]);this.showErrors();return this.valid();},checkForm:function(){this.prepareForm();for(var i=0,elements=(this.currentElements=this.elements());elements[i];i++){this.check(elements[i]);}return this.valid();},element:function(element){element=this.clean(element);this.lastElement=element;this.prepareElement(element);this.currentElements=$(element);var result=this.check(element);if(result){delete this.invalid[element.name];}else{this.invalid[element.name]=true;}if(!this.numberOfInvalids()){this.toHide=this.toHide.add(this.containers);}this.showErrors();return result;},showErrors:function(errors){if(errors){$.extend(this.errorMap,errors);this.errorList=[];for(var name in errors){this.errorList.push({message:errors[name],element:this.findByName(name)[0]});}this.successList=$.grep(this.successList,function(element){return!(element.name in errors);});}this.settings.showErrors?this.settings.showErrors.call(this,this.errorMap,this.errorList):this.defaultShowErrors();},resetForm:function(){if($.fn.resetForm)$(this.currentForm).resetForm();this.submitted={};this.prepareForm();this.hideErrors();this.elements().removeClass(this.settings.errorClass);},numberOfInvalids:function(){return this.objectLength(this.invalid);},objectLength:function(obj){var count=0;for(var i in obj)count++;return count;},hideErrors:function(){this.addWrapper(this.toHide).hide();},valid:function(){return this.size()==0;},size:function(){return this.errorList.length;},focusInvalid:function(){if(this.settings.focusInvalid){try{$(this.findLastActive()||this.errorList.length&&this.errorList[0].element||[]).filter(":visible").focus().trigger("focusin");}catch(e){}}},findLastActive:function(){var lastActive=this.lastActive;return lastActive&&$.grep(this.errorList,function(n){return n.element.name==lastActive.name;}).length==1&&lastActive;},elements:function(){var validator=this,rulesCache={};return $([]).add(this.currentForm.elements).filter(":input").not(":submit, :reset, :image, [disabled]").not(this.settings.ignore).filter(function(){!this.name&&validator.settings.debug&&window.console&&console.error("%o has no name assigned",this);if(this.name in rulesCache||!validator.objectLength($(this).rules()))return false;rulesCache[this.name]=true;return true;});},clean:function(selector){return $(selector)[0];},errors:function(){return $(this.settings.errorElement+"."+this.settings.errorClass,this.errorContext);},reset:function(){this.successList=[];this.errorList=[];this.errorMap={};this.toShow=$([]);this.toHide=$([]);this.currentElements=$([]);},prepareForm:function(){this.reset();this.toHide=this.errors().add(this.containers);},prepareElement:function(element){this.reset();this.toHide=this.errorsFor(element);},check:function(element){element=this.clean(element);if(this.checkable(element)){element=this.findByName(element.name)[0];}var rules=$(element).rules();var dependencyMismatch=false;for(method in rules){var rule={method:method,parameters:rules[method]};try{var result=$.validator.methods[method].call(this,element.value.replace(/\r/g,""),element,rule.parameters);if(result=="dependency-mismatch"){dependencyMismatch=true;continue;}dependencyMismatch=false;if(result=="pending"){this.toHide=this.toHide.not(this.errorsFor(element));return;}if(!result){this.formatAndAdd(element,rule);return false;}}catch(e){this.settings.debug&&window.console&&console.log("exception occured when checking element "+element.id
+", check the '"+rule.method+"' method",e);throw e;}}if(dependencyMismatch)return;if(this.objectLength(rules))this.successList.push(element);return true;},customMetaMessage:function(element,method){if(!$.metadata)return;var meta=this.settings.meta?$(element).metadata()[this.settings.meta]:$(element).metadata();return meta&&meta.messages&&meta.messages[method];},customMessage:function(name,method){var m=this.settings.messages[name];return m&&(m.constructor==String?m:m[method]);},findDefined:function(){for(var i=0;i<arguments.length;i++){if(arguments[i]!==undefined)return arguments[i];}return undefined;},defaultMessage:function(element,method){return this.findDefined(this.customMessage(element.name,method),this.customMetaMessage(element,method),!this.settings.ignoreTitle&&element.title||undefined,$.validator.messages[method],"<strong>Warning: No message defined for "+element.name+"</strong>");},formatAndAdd:function(element,rule){var message=this.defaultMessage(element,rule.method),theregex=/\$?\{(\d+)\}/g;if(typeof message=="function"){message=message.call(this,rule.parameters,element);}else if(theregex.test(message)){message=jQuery.format(message.replace(theregex,'{$1}'),rule.parameters);}this.errorList.push({message:message,element:element});this.errorMap[element.name]=message;this.submitted[element.name]=message;},addWrapper:function(toToggle){if(this.settings.wrapper)toToggle=toToggle.add(toToggle.parent(this.settings.wrapper));return toToggle;},defaultShowErrors:function(){for(var i=0;this.errorList[i];i++){var error=this.errorList[i];this.settings.highlight&&this.settings.highlight.call(this,error.element,this.settings.errorClass,this.settings.validClass);this.showLabel(error.element,error.message);}if(this.errorList.length){this.toShow=this.toShow.add(this.containers);}if(this.settings.success){for(var i=0;this.successList[i];i++){this.showLabel(this.successList[i]);}}if(this.settings.unhighlight){for(var i=0,elements=this.validElements();elements[i];i++){this.settings.unhighlight.call(this,elements[i],this.settings.errorClass,this.settings.validClass);}}this.toHide=this.toHide.not(this.toShow);this.hideErrors();this.addWrapper(this.toShow).show();},validElements:function(){return this.currentElements.not(this.invalidElements());},invalidElements:function(){return $(this.errorList).map(function(){return this.element;});},showLabel:function(element,message){var label=this.errorsFor(element);if(label.length){label.removeClass().addClass(this.settings.errorClass);label.attr("generated")&&label.html(message);}else{label=$("<"+this.settings.errorElement+"/>").attr({"for":this.idOrName(element),generated:true}).addClass(this.settings.errorClass).html(message||"");if(this.settings.wrapper){label=label.hide().show().wrap("<"+this.settings.wrapper+"/>").parent();}if(!this.labelContainer.append(label).length)this.settings.errorPlacement?this.settings.errorPlacement(label,$(element)):label.insertAfter(element);}if(!message&&this.settings.success){label.text("");typeof this.settings.success=="string"?label.addClass(this.settings.success):this.settings.success(label);}this.toShow=this.toShow.add(label);},errorsFor:function(element){var name=this.idOrName(element);return this.errors().filter(function(){return $(this).attr('for')==name;});},idOrName:function(element){return this.groups[element.name]||(this.checkable(element)?element.name:element.id||element.name);},checkable:function(element){return/radio|checkbox/i.test(element.type);},findByName:function(name){var form=this.currentForm;return $(document.getElementsByName(name)).map(function(index,element){return element.form==form&&element.name==name&&element||null;});},getLength:function(value,element){switch(element.nodeName.toLowerCase()){case'select':return $("option:selected",element).length;case'input':if(this.checkable(element))return this.findByName(element.name).filter(':checked').length;}return value.length;},depend:function(param,element){return this.dependTypes[typeof param]?this.dependTypes[typeof param](param,element):true;},dependTypes:{"boolean":function(param,element){return param;},"string":function(param,element){return!!$(param,element.form).length;},"function":function(param,element){return param(element);}},optional:function(element){return!$.validator.methods.required.call(this,$.trim(element.value),element)&&"dependency-mismatch";},startRequest:function(element){if(!this.pending[element.name]){this.pendingRequest++;this.pending[element.name]=true;}},stopRequest:function(element,valid){this.pendingRequest--;if(this.pendingRequest<0)this.pendingRequest=0;delete this.pending[element.name];if(valid&&this.pendingRequest==0&&this.formSubmitted&&this.form()){$(this.currentForm).submit();this.formSubmitted=false;}else if(!valid&&this.pendingRequest==0&&this.formSubmitted){$(this.currentForm).triggerHandler("invalid-form",[this]);this.formSubmitted=false;}},previousValue:function(element){return $.data(element,"previousValue")||$.data(element,"previousValue",{old:null,valid:true,message:this.defaultMessage(element,"remote")});}},classRuleSettings:{required:{required:true},email:{email:true},url:{url:true},date:{date:true},dateISO:{dateISO:true},dateDE:{dateDE:true},number:{number:true},numberDE:{numberDE:true},digits:{digits:true},creditcard:{creditcard:true}},addClassRules:function(className,rules){className.constructor==String?this.classRuleSettings[className]=rules:$.extend(this.classRuleSettings,className);},classRules:function(element){var rules={};var classes=$(element).attr('class');classes&&$.each(classes.split(' '),function(){if(this in $.validator.classRuleSettings){$.extend(rules,$.validator.classRuleSettings[this]);}});return rules;},attributeRules:function(element){var rules={};var $element=$(element);for(method in $.validator.methods){var value=$element.attr(method);if(value){rules[method]=value;}}if(rules.maxlength&&/-1|2147483647|524288/.test(rules.maxlength)){delete rules.maxlength;}return rules;},metadataRules:function(element){if(!$.metadata)return{};var meta=$.data(element.form,'validator').settings.meta;return meta?$(element).metadata()[meta]:$(element).metadata();},staticRules:function(element){var rules={};var validator=$.data(element.form,'validator');if(validator.settings.rules){rules=$.validator.normalizeRule(validator.settings.rules[element.name])||{};}return rules;},normalizeRules:function(rules,element){$.each(rules,function(prop,val){if(val===false){delete rules[prop];return;}if(val.param||val.depends){var keepRule=true;switch(typeof val.depends){case"string":keepRule=!!$(val.depends,element.form).length;break;case"function":keepRule=val.depends.call(element,element);break;}if(keepRule){rules[prop]=val.param!==undefined?val.param:true;}else{delete rules[prop];}}});$.each(rules,function(rule,parameter){rules[rule]=$.isFunction(parameter)?parameter(element):parameter;});$.each(['minlength','maxlength','min','max'],function(){if(rules[this]){rules[this]=Number(rules[this]);}});$.each(['rangelength','range'],function(){if(rules[this]){rules[this]=[Number(rules[this][0]),Number(rules[this][1])];}});if($.validator.autoCreateRanges){if(rules.min&&rules.max){rules.range=[rules.min,rules.max];delete rules.min;delete rules.max;}if(rules.minlength&&rules.maxlength){rules.rangelength=[rules.minlength,rules.maxlength];delete rules.minlength;delete rules.maxlength;}}if(rules.messages){delete rules.messages;}return rules;},normalizeRule:function(data){if(typeof data=="string"){var transformed={};$.each(data.split(/\s/),function(){transformed[this]=true;});data=transformed;}return data;},addMethod:function(name,method,message){$.validator.methods[name]=method;$.validator.messages[name]=message!=undefined?message:$.validator.messages[name];if(method.length<3){$.validator.addClassRules(name,$.validator.normalizeRule(name));}},methods:{required:function(value,element,param){if(!this.depend(param,element))return"dependency-mismatch";switch(element.nodeName.toLowerCase()){case'select':var val=$(element).val();return val&&val.length>0;case'input':if(this.checkable(element))return this.getLength(value,element)>0;default:return $.trim(value).length>0;}},remote:function(value,element,param){if(this.optional(element))return"dependency-mismatch";var previous=this.previousValue(element);if(!this.settings.messages[element.name])this.settings.messages[element.name]={};previous.originalMessage=this.settings.messages[element.name].remote;this.settings.messages[element.name].remote=previous.message;param=typeof param=="string"&&{url:param}||param;if(previous.old!==value){previous.old=value;var validator=this;this.startRequest(element);var data={};data[element.name]=value;$.ajax($.extend(true,{url:param,mode:"abort",port:"validate"+element.name,dataType:"json",data:data,success:function(response){validator.settings.messages[element.name].remote=previous.originalMessage;var valid=response===true;if(valid){var submitted=validator.formSubmitted;validator.prepareElement(element);validator.formSubmitted=submitted;validator.successList.push(element);validator.showErrors();}else{var errors={};var message=(previous.message=response||validator.defaultMessage(element,"remote"));errors[element.name]=$.isFunction(message)?message(value):message;validator.showErrors(errors);}previous.valid=valid;validator.stopRequest(element,valid);}},param));return"pending";}else if(this.pending[element.name]){return"pending";}return previous.valid;},minlength:function(value,element,param){return this.optional(element)||this.getLength($.trim(value),element)>=param;},maxlength:function(value,element,param){return this.optional(element)||this.getLength($.trim(value),element)<=param;},rangelength:function(value,element,param){var length=this.getLength($.trim(value),element);return this.optional(element)||(length>=param[0]&&length<=param[1]);},min:function(value,element,param){return this.optional(element)||value>=param;},max:function(value,element,param){return this.optional(element)||value<=param;},range:function(value,element,param){return this.optional(element)||(value>=param[0]&&value<=param[1]);},email:function(value,element){return this.optional(element)||/^((([a-z]|\d|[!#\$%&'\*\+\-\/=\?\^_`{\|}~]|[\u00A0-\uD7FF\uF900-\uFDCF\uFDF0-\uFFEF])+(\.([a-z]|\d|[!#\$%&'\*\+\-\/=\?\^_`{\|}~]|[\u00A0-\uD7FF\uF900-\uFDCF\uFDF0-\uFFEF])+)*)|((\x22)((((\x20|\x09)*(\x0d\x0a))?(\x20|\x09)+)?(([\x01-\x08\x0b\x0c\x0e-\x1f\x7f]|\x21|[\x23-\x5b]|[\x5d-\x7e]|[\u00A0-\uD7FF\uF900-\uFDCF\uFDF0-\uFFEF])|(\\([\x01-\x09\x0b\x0c\x0d-\x7f]|[\u00A0-\uD7FF\uF900-\uFDCF\uFDF0-\uFFEF]))))*(((\x20|\x09)*(\x0d\x0a))?(\x20|\x09)+)?(\x22)))@((([a-z]|\d|[\u00A0-\uD7FF\uF900-\uFDCF\uFDF0-\uFFEF])|(([a-z]|\d|[\u00A0-\uD7FF\uF900-\uFDCF\uFDF0-\uFFEF])([a-z]|\d|-|\.|_|~|[\u00A0-\uD7FF\uF900-\uFDCF\uFDF0-\uFFEF])*([a-z]|\d|[\u00A0-\uD7FF\uF900-\uFDCF\uFDF0-\uFFEF])))\.)+(([a-z]|[\u00A0-\uD7FF\uF900-\uFDCF\uFDF0-\uFFEF])|(([a-z]|[\u00A0-\uD7FF\uF900-\uFDCF\uFDF0-\uFFEF])([a-z]|\d|-|\.|_|~|[\u00A0-\uD7FF\uF900-\uFDCF\uFDF0-\uFFEF])*([a-z]|[\u00A0-\uD7FF\uF900-\uFDCF\uFDF0-\uFFEF])))\.?$/i.test(value);},url:function(value,element){return this.optional(element)||/^(https?|ftp):\/\/(((([a-z]|\d|-|\.|_|~|[\u00A0-\uD7FF\uF900-\uFDCF\uFDF0-\uFFEF])|(%[\da-f]{2})|[!\$&'\(\)\*\+,;=]|:)*@)?(((\d|[1-9]\d|1\d\d|2[0-4]\d|25[0-5])\.(\d|[1-9]\d|1\d\d|2[0-4]\d|25[0-5])\.(\d|[1-9]\d|1\d\d|2[0-4]\d|25[0-5])\.(\d|[1-9]\d|1\d\d|2[0-4]\d|25[0-5]))|((([a-z]|\d|[\u00A0-\uD7FF\uF900-\uFDCF\uFDF0-\uFFEF])|(([a-z]|\d|[\u00A0-\uD7FF\uF900-\uFDCF\uFDF0-\uFFEF])([a-z]|\d|-|\.|_|~|[\u00A0-\uD7FF\uF900-\uFDCF\uFDF0-\uFFEF])*([a-z]|\d|[\u00A0-\uD7FF\uF900-\uFDCF\uFDF0-\uFFEF])))\.)+(([a-z]|[\u00A0-\uD7FF\uF900-\uFDCF\uFDF0-\uFFEF])|(([a-z]|[\u00A0-\uD7FF\uF900-\uFDCF\uFDF0-\uFFEF])([a-z]|\d|-|\.|_|~|[\u00A0-\uD7FF\uF900-\uFDCF\uFDF0-\uFFEF])*([a-z]|[\u00A0-\uD7FF\uF900-\uFDCF\uFDF0-\uFFEF])))\.?)(:\d*)?)(\/((([a-z]|\d|-|\.|_|~|[\u00A0-\uD7FF\uF900-\uFDCF\uFDF0-\uFFEF])|(%[\da-f]{2})|[!\$&'\(\)\*\+,;=]|:|@)+(\/(([a-z]|\d|-|\.|_|~|[\u00A0-\uD7FF\uF900-\uFDCF\uFDF0-\uFFEF])|(%[\da-f]{2})|[!\$&'\(\)\*\+,;=]|:|@)*)*)?)?(\?((([a-z]|\d|-|\.|_|~|[\u00A0-\uD7FF\uF900-\uFDCF\uFDF0-\uFFEF])|(%[\da-f]{2})|[!\$&'\(\)\*\+,;=]|:|@)|[\uE000-\uF8FF]|\/|\?)*)?(\#((([a-z]|\d|-|\.|_|~|[\u00A0-\uD7FF\uF900-\uFDCF\uFDF0-\uFFEF])|(%[\da-f]{2})|[!\$&'\(\)\*\+,;=]|:|@)|\/|\?)*)?$/i.test(value);},date:function(value,element){return this.optional(element)||!/Invalid|NaN/.test(new Date(value));},dateISO:function(value,element){return this.optional(element)||/^\d{4}[\/-]\d{1,2}[\/-]\d{1,2}$/.test(value);},number:function(value,element){return this.optional(element)||/^-?(?:\d+|\d{1,3}(?:,\d{3})+)(?:\.\d+)?$/.test(value);},digits:function(value,element){return this.optional(element)||/^\d+$/.test(value);},creditcard:function(value,element){if(this.optional(element))return"dependency-mismatch";if(/[^0-9-]+/.test(value))return false;var nCheck=0,nDigit=0,bEven=false;value=value.replace(/\D/g,"");for(var n=value.length-1;n>=0;n--){var cDigit=value.charAt(n);var nDigit=parseInt(cDigit,10);if(bEven){if((nDigit*=2)>9)nDigit-=9;}nCheck+=nDigit;bEven=!bEven;}return(nCheck%10)==0;},accept:function(value,element,param){param=typeof param=="string"?param.replace(/,/g,'|'):"png|jpe?g|gif";return this.optional(element)||value.match(new RegExp(".("+param+")$","i"));},equalTo:function(value,element,param){var target=$(param).unbind(".validate-equalTo").bind("blur.validate-equalTo",function(){$(element).valid();});return value==target.val();}}});$.format=$.validator.format;})(jQuery);;(function($){var ajax=$.ajax;var pendingRequests={};$.ajax=function(settings){settings=$.extend(settings,$.extend({},$.ajaxSettings,settings));var port=settings.port;if(settings.mode=="abort"){if(pendingRequests[port]){pendingRequests[port].abort();}return(pendingRequests[port]=ajax.apply(this,arguments));}return ajax.apply(this,arguments);};})(jQuery);;(function($){if(!jQuery.event.special.focusin&&!jQuery.event.special.focusout&&document.addEventListener){$.each({focus:'focusin',blur:'focusout'},function(original,fix){$.event.special[fix]={setup:function(){this.addEventListener(original,handler,true);},teardown:function(){this.removeEventListener(original,handler,true);},handler:function(e){arguments[0]=$.event.fix(e);arguments[0].type=fix;return $.event.handle.apply(this,arguments);}};function handler(e){e=$.event.fix(e);e.type=fix;return $.event.handle.call(this,e);}});};$.extend($.fn,{validateDelegate:function(delegate,type,handler){return this.bind(type,function(event){var target=$(event.target);if(target.is(delegate)){return handler.apply(target,arguments);}});}});})(jQuery);
/*
 * Modernizr v1.6
 * http://www.modernizr.com
 *
 * Developed by: 
 * - Faruk Ates  http://farukat.es/
 * - Paul Irish  http://paulirish.com/
 *
 * Copyright (c) 2009-2010
 * Dual-licensed under the BSD or MIT licenses.
 * http://www.modernizr.com/license/
 */
window.Modernizr=function(i,e,u){function s(a,b){return(""+a).indexOf(b)!==-1}function D(a,b){for(var c in a)if(j[a[c]]!==u&&(!b||b(a[c],E)))return true}function n(a,b){var c=a.charAt(0).toUpperCase()+a.substr(1);c=(a+" "+F.join(c+" ")+c).split(" ");return!!D(c,b)}function S(){f.input=function(a){for(var b=0,c=a.length;b<c;b++)L[a[b]]=!!(a[b]in h);return L}("autocomplete autofocus list placeholder max min multiple pattern required step".split(" "));f.inputtypes=function(a){for(var b=0,c,k=a.length;b<
k;b++){h.setAttribute("type",a[b]);if(c=h.type!=="text"){h.value=M;if(/^range$/.test(h.type)&&h.style.WebkitAppearance!==u){l.appendChild(h);c=e.defaultView;c=c.getComputedStyle&&c.getComputedStyle(h,null).WebkitAppearance!=="textfield"&&h.offsetHeight!==0;l.removeChild(h)}else/^(search|tel)$/.test(h.type)||(c=/^(url|email)$/.test(h.type)?h.checkValidity&&h.checkValidity()===false:h.value!=M)}N[a[b]]=!!c}return N}("search tel url email datetime date month week time datetime-local number range color".split(" "))}
var f={},l=e.documentElement,E=e.createElement("modernizr"),j=E.style,h=e.createElement("input"),M=":)",O=Object.prototype.toString,q=" -webkit- -moz- -o- -ms- -khtml- ".split(" "),F="Webkit Moz O ms Khtml".split(" "),v={svg:"http://www.w3.org/2000/svg"},d={},N={},L={},P=[],w,Q=function(a){var b=document.createElement("style"),c=e.createElement("div");b.textContent=a+"{#modernizr{height:3px}}";(e.head||e.getElementsByTagName("head")[0]).appendChild(b);c.id="modernizr";l.appendChild(c);a=c.offsetHeight===
3;b.parentNode.removeChild(b);c.parentNode.removeChild(c);return!!a},o=function(){var a={select:"input",change:"input",submit:"form",reset:"form",error:"img",load:"img",abort:"img"};return function(b,c){c=c||document.createElement(a[b]||"div");b="on"+b;var k=b in c;if(!k){c.setAttribute||(c=document.createElement("div"));if(c.setAttribute&&c.removeAttribute){c.setAttribute(b,"");k=typeof c[b]=="function";if(typeof c[b]!="undefined")c[b]=u;c.removeAttribute(b)}}return k}}(),G={}.hasOwnProperty,R;R=
typeof G!=="undefined"&&typeof G.call!=="undefined"?function(a,b){return G.call(a,b)}:function(a,b){return b in a&&typeof a.constructor.prototype[b]==="undefined"};d.flexbox=function(){var a=e.createElement("div"),b=e.createElement("div");(function(k,g,r,x){g+=":";k.style.cssText=(g+q.join(r+";"+g)).slice(0,-g.length)+(x||"")})(a,"display","box","width:42px;padding:0;");b.style.cssText=q.join("box-flex:1;")+"width:10px;";a.appendChild(b);l.appendChild(a);var c=b.offsetWidth===42;a.removeChild(b);
l.removeChild(a);return c};d.canvas=function(){var a=e.createElement("canvas");return!!(a.getContext&&a.getContext("2d"))};d.canvastext=function(){return!!(f.canvas&&typeof e.createElement("canvas").getContext("2d").fillText=="function")};d.webgl=function(){var a=e.createElement("canvas");try{if(a.getContext("webgl"))return true}catch(b){}try{if(a.getContext("experimental-webgl"))return true}catch(c){}return false};d.touch=function(){return"ontouchstart"in i||Q("@media ("+q.join("touch-enabled),(")+
"modernizr)")};d.geolocation=function(){return!!navigator.geolocation};d.postmessage=function(){return!!i.postMessage};d.websqldatabase=function(){return!!i.openDatabase};d.indexedDB=function(){for(var a=-1,b=F.length;++a<b;){var c=F[a].toLowerCase();if(i[c+"_indexedDB"]||i[c+"IndexedDB"])return true}return false};d.hashchange=function(){return o("hashchange",i)&&(document.documentMode===u||document.documentMode>7)};d.history=function(){return!!(i.history&&history.pushState)};d.draganddrop=function(){return o("drag")&&
o("dragstart")&&o("dragenter")&&o("dragover")&&o("dragleave")&&o("dragend")&&o("drop")};d.websockets=function(){return"WebSocket"in i};d.rgba=function(){j.cssText="background-color:rgba(150,255,150,.5)";return s(j.backgroundColor,"rgba")};d.hsla=function(){j.cssText="background-color:hsla(120,40%,100%,.5)";return s(j.backgroundColor,"rgba")||s(j.backgroundColor,"hsla")};d.multiplebgs=function(){j.cssText="background:url(//:),url(//:),red url(//:)";return/(url\s*\(.*?){3}/.test(j.background)};d.backgroundsize=
function(){return n("backgroundSize")};d.borderimage=function(){return n("borderImage")};d.borderradius=function(){return n("borderRadius","",function(a){return s(a,"orderRadius")})};d.boxshadow=function(){return n("boxShadow")};d.textshadow=function(){return e.createElement("div").style.textShadow===""};d.opacity=function(){var a=q.join("opacity:.5;")+"";j.cssText=a;return s(j.opacity,"0.5")};d.cssanimations=function(){return n("animationName")};d.csscolumns=function(){return n("columnCount")};d.cssgradients=
function(){var a=("background-image:"+q.join("gradient(linear,left top,right bottom,from(#9f9),to(white));background-image:")+q.join("linear-gradient(left top,#9f9, white);background-image:")).slice(0,-17);j.cssText=a;return s(j.backgroundImage,"gradient")};d.cssreflections=function(){return n("boxReflect")};d.csstransforms=function(){return!!D(["transformProperty","WebkitTransform","MozTransform","OTransform","msTransform"])};d.csstransforms3d=function(){var a=!!D(["perspectiveProperty","WebkitPerspective",
"MozPerspective","OPerspective","msPerspective"]);if(a)a=Q("@media ("+q.join("transform-3d),(")+"modernizr)");return a};d.csstransitions=function(){return n("transitionProperty")};d.fontface=function(){var a,b=e.head||e.getElementsByTagName("head")[0]||l,c=e.createElement("style"),k=e.implementation||{hasFeature:function(){return false}};c.type="text/css";b.insertBefore(c,b.firstChild);a=c.sheet||c.styleSheet;b=k.hasFeature("CSS2","")?function(g){if(!(a&&g))return false;var r=false;try{a.insertRule(g,
0);r=!/unknown/i.test(a.cssRules[0].cssText);a.deleteRule(a.cssRules.length-1)}catch(x){}return r}:function(g){if(!(a&&g))return false;a.cssText=g;return a.cssText.length!==0&&!/unknown/i.test(a.cssText)&&a.cssText.replace(/\r+|\n+/g,"").indexOf(g.split(" ")[0])===0};f._fontfaceready=function(g){g(f.fontface)};return b('@font-face { font-family: "font"; src: "font.ttf"; }')};d.video=function(){var a=e.createElement("video"),b=!!a.canPlayType;if(b){b=new Boolean(b);b.ogg=a.canPlayType('video/ogg; codecs="theora"');
b.h264=a.canPlayType('video/mp4; codecs="avc1.42E01E"')||a.canPlayType('video/mp4; codecs="avc1.42E01E, mp4a.40.2"');b.webm=a.canPlayType('video/webm; codecs="vp8, vorbis"')}return b};d.audio=function(){var a=e.createElement("audio"),b=!!a.canPlayType;if(b){b=new Boolean(b);b.ogg=a.canPlayType('audio/ogg; codecs="vorbis"');b.mp3=a.canPlayType("audio/mpeg;");b.wav=a.canPlayType('audio/wav; codecs="1"');b.m4a=a.canPlayType("audio/x-m4a;")||a.canPlayType("audio/aac;")}return b};d.localstorage=function(){try{return"localStorage"in
i&&i.localStorage!==null}catch(a){return false}};d.sessionstorage=function(){try{return"sessionStorage"in i&&i.sessionStorage!==null}catch(a){return false}};d.webWorkers=function(){return!!i.Worker};d.applicationcache=function(){return!!i.applicationCache};d.svg=function(){return!!e.createElementNS&&!!e.createElementNS(v.svg,"svg").createSVGRect};d.inlinesvg=function(){var a=document.createElement("div");a.innerHTML="<svg/>";return(a.firstChild&&a.firstChild.namespaceURI)==v.svg};d.smil=function(){return!!e.createElementNS&&
/SVG/.test(O.call(e.createElementNS(v.svg,"animate")))};d.svgclippaths=function(){return!!e.createElementNS&&/SVG/.test(O.call(e.createElementNS(v.svg,"clipPath")))};for(var H in d)if(R(d,H)){w=H.toLowerCase();f[w]=d[H]();P.push((f[w]?"":"no-")+w)}f.input||S();f.crosswindowmessaging=f.postmessage;f.historymanagement=f.history;f.addTest=function(a,b){a=a.toLowerCase();if(!f[a]){b=!!b();l.className+=" "+(b?"":"no-")+a;f[a]=b;return f}};j.cssText="";E=h=null;i.attachEvent&&function(){var a=e.createElement("div");
a.innerHTML="<elem></elem>";return a.childNodes.length!==1}()&&function(a,b){function c(p){for(var m=-1;++m<r;)p.createElement(g[m])}function k(p,m){for(var I=p.length,t=-1,y,J=[];++t<I;){y=p[t];m=y.media||m;J.push(k(y.imports,m));J.push(y.cssText)}return J.join("")}var g="abbr|article|aside|audio|canvas|details|figcaption|figure|footer|header|hgroup|mark|meter|nav|output|progress|section|summary|time|video".split("|"),r=g.length,x=RegExp("<(/*)(abbr|article|aside|audio|canvas|details|figcaption|figure|footer|header|hgroup|mark|meter|nav|output|progress|section|summary|time|video)",
"gi"),T=RegExp("\\b(abbr|article|aside|audio|canvas|details|figcaption|figure|footer|header|hgroup|mark|meter|nav|output|progress|section|summary|time|video)\\b(?!.*[;}])","gi"),z=b.createDocumentFragment(),A=b.documentElement,K=A.firstChild,B=b.createElement("style"),C=b.createElement("body");B.media="all";c(b);c(z);a.attachEvent("onbeforeprint",function(){for(var p=-1;++p<r;)for(var m=b.getElementsByTagName(g[p]),I=m.length,t=-1;++t<I;)if(m[t].className.indexOf("iepp_")<0)m[t].className+=" iepp_"+
g[p];K.insertBefore(B,K.firstChild);B.styleSheet.cssText=k(b.styleSheets,"all").replace(T,".iepp_$1");z.appendChild(b.body);A.appendChild(C);C.innerHTML=z.firstChild.innerHTML.replace(x,"<$1bdo")});a.attachEvent("onafterprint",function(){C.innerHTML="";A.removeChild(C);K.removeChild(B);A.appendChild(z.firstChild)})}(this,document);f._enableHTML5=true;f._version="1.6";l.className=l.className.replace(/\bno-js\b/,"")+" js";l.className+=" "+P.join(" ");return f}(this,this.document);
/*
  mustache.js — Logic-less templates in JavaScript

  See http://mustache.github.com/ for more info.
*/

var Mustache = function() {
  var regexCache = {};
  var Renderer = function() {};

  Renderer.prototype = {
    otag: "{{",
    ctag: "}}",
    pragmas: {},
    buffer: [],
    pragmas_implemented: {
      "IMPLICIT-ITERATOR": true
    },
    context: {},

    render: function(template, context, partials, in_recursion) {
      // reset buffer & set context
      if(!in_recursion) {
        this.context = context;
        this.buffer = []; // TODO: make this non-lazy
      }

      // fail fast
      if(!this.includes("", template)) {
        if(in_recursion) {
          return template;
        } else {
          this.send(template);
          return;
        }
      }

      // get the pragmas together
      template = this.render_pragmas(template);

      // render the template
      var html = this.render_section(template, context, partials);

      // render_section did not find any sections, we still need to render the tags
      if (html === false) {
        html = this.render_tags(template, context, partials, in_recursion);
      }

      if (in_recursion) {
        return html;
      } else {
        this.sendLines(html);
      }
    },

    /*
      Sends parsed lines
    */
    send: function(line) {
      if(line !== "") {
        this.buffer.push(line);
      }
    },

    sendLines: function(text) {
      if (text) {
        var lines = text.split("\n");
        for (var i = 0; i < lines.length; i++) {
          this.send(lines[i]);
        }
      }
    },

    /*
      Looks for %PRAGMAS
    */
    render_pragmas: function(template) {
      // no pragmas
      if(!this.includes("%", template)) {
        return template;
      }

      var that = this;
      var regex = this.getCachedRegex("render_pragmas", function(otag, ctag) {
        return new RegExp(otag + "%([\\w-]+) ?([\\w]+=[\\w]+)?" + ctag, "g");
      });

      return template.replace(regex, function(match, pragma, options) {
        if(!that.pragmas_implemented[pragma]) {
          throw({message:
            "This implementation of mustache doesn't understand the '" +
            pragma + "' pragma"});
        }
        that.pragmas[pragma] = {};
        if(options) {
          var opts = options.split("=");
          that.pragmas[pragma][opts[0]] = opts[1];
        }
        return "";
        // ignore unknown pragmas silently
      });
    },

    /*
      Tries to find a partial in the curent scope and render it
    */
    render_partial: function(name, context, partials) {
      name = this.trim(name);
      if(!partials || partials[name] === undefined) {
        throw({message: "unknown_partial '" + name + "'"});
      }
      if(typeof(context[name]) != "object") {
        return this.render(partials[name], context, partials, true);
      }
      return this.render(partials[name], context[name], partials, true);
    },

    /*
      Renders inverted (^) and normal (#) sections
    */
    render_section: function(template, context, partials) {
      if(!this.includes("#", template) && !this.includes("^", template)) {
        // did not render anything, there were no sections
        return false;
      }

      var that = this;

      var regex = this.getCachedRegex("render_section", function(otag, ctag) {
        // This regex matches _the first_ section ({{#foo}}{{/foo}}), and captures the remainder
        return new RegExp(
          "^([\\s\\S]*?)" +         // all the crap at the beginning that is not {{*}} ($1)

          otag +                    // {{
          "(\\^|\\#)\\s*(.+)\\s*" + //  #foo (# == $2, foo == $3)
          ctag +                    // }}

          "\n*([\\s\\S]*?)" +       // between the tag ($2). leading newlines are dropped

          otag +                    // {{
          "\\/\\s*\\3\\s*" +        //  /foo (backreference to the opening tag).
          ctag +                    // }}

          "\\s*([\\s\\S]*)$",       // everything else in the string ($4). leading whitespace is dropped.

        "g");
      });


      // for each {{#foo}}{{/foo}} section do...
      return template.replace(regex, function(match, before, type, name, content, after) {
        // before contains only tags, no sections
        var renderedBefore = before ? that.render_tags(before, context, partials, true) : "",

        // after may contain both sections and tags, so use full rendering function
            renderedAfter = after ? that.render(after, context, partials, true) : "",

        // will be computed below
            renderedContent,

            value = that.find(name, context);

        if (type === "^") { // inverted section
          if (!value || that.is_array(value) && value.length === 0) {
            // false or empty list, render it
            renderedContent = that.render(content, context, partials, true);
          } else {
            renderedContent = "";
          }
        } else if (type === "#") { // normal section
          if (that.is_array(value)) { // Enumerable, Let's loop!
            renderedContent = that.map(value, function(row) {
              return that.render(content, that.create_context(row), partials, true);
            }).join("");
          } else if (that.is_object(value)) { // Object, Use it as subcontext!
            renderedContent = that.render(content, that.create_context(value),
              partials, true);
          } else if (typeof value === "function") {
            // higher order section
            renderedContent = value.call(context, content, function(text) {
              return that.render(text, context, partials, true);
            });
          } else if (value) { // boolean section
            renderedContent = that.render(content, context, partials, true);
          } else {
            renderedContent = "";
          }
        }

        return renderedBefore + renderedContent + renderedAfter;
      });
    },

    /*
      Replace {{foo}} and friends with values from our view
    */
    render_tags: function(template, context, partials, in_recursion) {
      // tit for tat
      var that = this;



      var new_regex = function() {
        return that.getCachedRegex("render_tags", function(otag, ctag) {
          return new RegExp(otag + "(=|!|>|\\{|%)?([^\\/#\\^]+?)\\1?" + ctag + "+", "g");
        });
      };

      var regex = new_regex();
      var tag_replace_callback = function(match, operator, name) {
        switch(operator) {
        case "!": // ignore comments
          return "";
        case "=": // set new delimiters, rebuild the replace regexp
          that.set_delimiters(name);
          regex = new_regex();
          return "";
        case ">": // render partial
          return that.render_partial(name, context, partials);
        case "{": // the triple mustache is unescaped
          return that.find(name, context);
        default: // escape the value
          return that.escape(that.find(name, context));
        }
      };
      var lines = template.split("\n");
      for(var i = 0; i < lines.length; i++) {
        lines[i] = lines[i].replace(regex, tag_replace_callback, this);
        if(!in_recursion) {
          this.send(lines[i]);
        }
      }

      if(in_recursion) {
        return lines.join("\n");
      }
    },

    set_delimiters: function(delimiters) {
      var dels = delimiters.split(" ");
      this.otag = this.escape_regex(dels[0]);
      this.ctag = this.escape_regex(dels[1]);
    },

    escape_regex: function(text) {
      // thank you Simon Willison
      if(!arguments.callee.sRE) {
        var specials = [
          '/', '.', '*', '+', '?', '|',
          '(', ')', '[', ']', '{', '}', '\\'
        ];
        arguments.callee.sRE = new RegExp(
          '(\\' + specials.join('|\\') + ')', 'g'
        );
      }
      return text.replace(arguments.callee.sRE, '\\$1');
    },

    /*
      find `name` in current `context`. That is find me a value
      from the view object
    */
    find: function(name, context) {
      name = this.trim(name);

      // Checks whether a value is thruthy or false or 0
      function is_kinda_truthy(bool) {
        return bool === false || bool === 0 || bool;
      }

      var value;
      
      // check for dot notation eg. foo.bar
      if(name.match(/([a-z_]+)\./ig)){
        var childValue = this.walk_context(name, context);
        if(is_kinda_truthy(childValue)) {
          value = childValue;
        }
      }
      else{
        if(is_kinda_truthy(context[name])) {
          value = context[name];
        } else if(is_kinda_truthy(this.context[name])) {
          value = this.context[name];
        }
      }

      if(typeof value === "function") {
        return value.apply(context);
      }
      if(value !== undefined) {
        return value;
      }
      // silently ignore unkown variables
      return "";
    },

    walk_context: function(name, context){
      var path = name.split('.');
      // if the var doesn't exist in current context, check the top level context
      var value_context = (context[path[0]] != undefined) ? context : this.context;
      var value = value_context[path.shift()];
      while(value != undefined && path.length > 0){
        value_context = value;
        value = value[path.shift()];
      }
      // if the value is a function, call it, binding the correct context
      if(typeof value === "function") {
        return value.apply(value_context);
      }
      return value;
    },

    // Utility methods

    /* includes tag */
    includes: function(needle, haystack) {
      return haystack.indexOf(this.otag + needle) != -1;
    },

    /*
      Does away with nasty characters
    */
    escape: function(s) {
      s = String(s === null ? "" : s);
      return s.replace(/&(?!\w+;)|["'<>\\]/g, function(s) {
        switch(s) {
        case "&": return "&amp;";
        case '"': return '&quot;';
        case "'": return '&#39;';
        case "<": return "&lt;";
        case ">": return "&gt;";
        default: return s;
        }
      });
    },

    // by @langalex, support for arrays of strings
    create_context: function(_context) {
      if(this.is_object(_context)) {
        return _context;
      } else {
        var iterator = ".";
        if(this.pragmas["IMPLICIT-ITERATOR"]) {
          iterator = this.pragmas["IMPLICIT-ITERATOR"].iterator;
        }
        var ctx = {};
        ctx[iterator] = _context;
        return ctx;
      }
    },

    is_object: function(a) {
      return a && typeof a == "object";
    },

    is_array: function(a) {
      return Object.prototype.toString.call(a) === '[object Array]';
    },

    /*
      Gets rid of leading and trailing whitespace
    */
    trim: function(s) {
      return s.replace(/^\s*|\s*$/g, "");
    },

    /*
      Why, why, why? Because IE. Cry, cry cry.
    */
    map: function(array, fn) {
      if (typeof array.map == "function") {
        return array.map(fn);
      } else {
        var r = [];
        var l = array.length;
        for(var i = 0; i < l; i++) {
          r.push(fn(array[i]));
        }
        return r;
      }
    },

    getCachedRegex: function(name, generator) {
      var byOtag = regexCache[this.otag];
      if (!byOtag) {
        byOtag = regexCache[this.otag] = {};
      }

      var byCtag = byOtag[this.ctag];
      if (!byCtag) {
        byCtag = byOtag[this.ctag] = {};
      }

      var regex = byCtag[name];
      if (!regex) {
        regex = byCtag[name] = generator(this.otag, this.ctag);
      }

      return regex;
    }
  };

  return({
    name: "mustache.js",
    version: "0.4.0-dev",

    /*
      Turns a template and view into HTML
    */
    to_html: function(template, view, partials, send_fun) {
      var renderer = new Renderer();
      if(send_fun) {
        renderer.send = send_fun;
      }
      renderer.render(template, view || {}, partials);
      if(!send_fun) {
        return renderer.buffer.join("\n");
      }
    }
  });
}();
/*
 * jQuery Plugin: Tokenizing Autocomplete Text Entry
 * Version 1.1
 *
 * Copyright (c) 2009 James Smith (http://loopj.com)
 * Licensed jointly under the GPL and MIT licenses,
 * choose which one suits your project best!
 *
 */

(function($) {

$.fn.tokenInput = function (url, options) {
    var settings = $.extend({
        url: url,
        hintText: "Type in a search term",
        noResultsText: "No results",
        searchingText: "Searching...",
        searchDelay: 300,
        minChars: 1,
        tokenLimit: null,
        jsonContainer: null,
        method: "GET",
        contentType: "json",
        queryParam: "q",
        onResult: null,
        onAdd: null,
        onDelete: null,
        doImmediate:true,
        country:'US',
        featureClass: null,
        featureCode:null,
        maxRows: 10
   }, options);

    settings.classes = $.extend({
        tokenList: "token-input-list",
        token: "token-input-token",
        tokenDelete: "token-input-delete-token",
        selectedToken: "token-input-selected-token",
        highlightedToken: "token-input-highlighted-token",
        dropdown: "token-input-dropdown",
        dropdownItem: "token-input-dropdown-item",
        dropdownItem2: "token-input-dropdown-item2",
        selectedDropdownItem: "token-input-selected-dropdown-item",
        inputToken: "token-input-input-token"
    }, options.classes);

    return this.each(function () {
        var list = new $.TokenList(this, settings);
    });
};

$.TokenData = function(data,type) {
    var raw = data;
    var name;
    var input;
    var id;
    var code;
    function city_input() {
        var value = raw.lat + ',' + raw.lng + ':' + raw.adminCode1 + ':' + raw.name + ':' + raw.countryCode;
        return $('<input type="hidden" class="' + raw.countryCode + '" name="cities" id="' + raw.name.replace(/ /gi, '_') + '" value="' + value + '" />');
    }
    function country_input() {
        return $('<input type="hidden" name="geo_predicates" id="' + code + '" value="' + code + '" />');
    }

    if (type == 'city') {
        name = raw.name + ", " + raw.adminCode1;
        input = city_input;
        id = raw.name;
    }
    else if (type == 'country') {
        code = (raw.data === undefined) ? raw.code : raw.data.code;
        name = (raw.data === undefined) ? raw.name : raw.data.name;
        input = country_input;
        id = code;
    }


    return {
        name: name,
        input: input,
        raw: data,
        type: type,
        id: id
    };
};

$.TokenList = function (input, settings) {
    //
    // Variables
    //
    // Input box position "enum"
    var POSITION = {
        BEFORE: 0,
        AFTER: 1,
        END: 2
    };

    // Keys "enum"
    var KEY = {
        BACKSPACE: 8,
        TAB: 9,
        RETURN: 13,
        ESC: 27,
        LEFT: 37,
        UP: 38,
        RIGHT: 39,
        DOWN: 40,
        COMMA: 188
    };

    // Save the tokens
    var saved_tokens = [];

    // Keep track of the number of tokens in the list
    var token_count = 0;
    var token_id    = 0;

    // Basic cache to save on db hits
    var cache = new $.TokenList.Cache( settings );

    // Keep track of the timeout
    var timeout;

    // Create a new text input an attach keyup events
    var input_box = $("<input class=\"token-input-field\" type=\"text\"  autocomplete=\"off\">")
        .css({
            outline: "none"
        })
        .focus(function () {
            if (settings.tokenLimit === null || settings.tokenLimit != token_count) {
                show_dropdown_hint();
            }
            $(this).addClass('focused');
            if( !token_list.hasClass('focused')) {
                token_list.addClass('focused');
            }
            if( $(this).val() ) {
              setTimeout(function(){do_search(settings.doImmediate);}, 5);
           }
        })
        .blur(function () {
            $(this).removeClass('focused');
            token_list.removeClass('focused');
            hide_dropdown();
        })
        .keydown(function (event) {
            var previous_token;
            var next_token;

            switch(event.keyCode) {
                case KEY.LEFT:
                case KEY.RIGHT:
                case KEY.UP:
                case KEY.DOWN:
                    if(!$(this).val()) {
                        previous_token = input_token.prev();
                        next_token = input_token.next();

                        if((previous_token.length && previous_token.get(0) === selected_token) || (next_token.length && next_token.get(0) === selected_token)) {
                            // Check if there is a previous/next token and it is selected
                            if(event.keyCode == KEY.LEFT || event.keyCode == KEY.UP) {
                                deselect_token($(selected_token), POSITION.BEFORE);
                            } else {
                                deselect_token($(selected_token), POSITION.AFTER);
                            }
                        } else if((event.keyCode == KEY.LEFT || event.keyCode == KEY.UP) && previous_token.length) {
                            // We are moving left, select the previous token if it exists
                            select_token($(previous_token.get(0)));
                        } else if((event.keyCode == KEY.RIGHT || event.keyCode == KEY.DOWN) && next_token.length) {
                            // We are moving right, select the next token if it exists
                            select_token($(next_token.get(0)));
                        }
                    } else {
                        var dropdown_item = null;

                        if(event.keyCode == KEY.DOWN || event.keyCode == KEY.RIGHT) {
                            dropdown_item = $(selected_dropdown_item).next();
                        } else {
                            dropdown_item = $(selected_dropdown_item).prev();
                        }

                        if(dropdown_item.length) {
                            select_dropdown_item(dropdown_item);
                        }
                        return false;
                    }
                    break;

                case KEY.BACKSPACE:
                    previous_token = input_token.prev();

                    if(!$(this).val().length) {
                        if(selected_token) {
                            delete_token($(selected_token));
                        } else if(previous_token.length) {
                            select_token($(previous_token.get(0)));
                        }

                        return false;
                    } else if($(this).val().length == 1) {
                        hide_dropdown();
                    } else {
                        // set a timeout just long enough to let this function finish.
                        setTimeout(function(){do_search(settings.doImmediate);}, 5);
                   }
                    break;

                case KEY.TAB:
                case KEY.RETURN:
                case KEY.COMMA:
                  if(selected_dropdown_item) {
                    add_token($(selected_dropdown_item));
                    return false;
                  }
                  break;

                case KEY.ESC:
                  hide_dropdown();
                  return true;

                default:
                    if(is_printable_character(event.keyCode)) {
                      // set a timeout just long enough to let this function finish.
                      setTimeout(function(){do_search(settings.doImmediate);}, 5);
                    }
                    break;
            }
        });

    // Keep a reference to the original input box
    var hidden_input = $(input)
                           .hide()
                           .focus(function () {
                               input_box.focus();
                           })
                           .blur(function () {
                               input_box.blur();
                           });

    // Keep a reference to the selected token and dropdown item
    var selected_token = null;
    var selected_dropdown_item = null;

    // The list to store the token items in
    var token_list = $("<ul />")
        .addClass(settings.classes.tokenList)
        .insertBefore(hidden_input)
        .click(function (event) {
            $(this).addClass('focused');
            var li = get_element_from_event(event, "li");
            if(li && li.get(0) != input_token.get(0)) {
                toggle_select_token(li);
                return false;
            } else {
                input_box.focus();

                if(selected_token) {
                    deselect_token($(selected_token), POSITION.END);
                }
            }
        })
        .mouseover(function (event) {
            var li = get_element_from_event(event, "li");
            if(li && selected_token !== this) {
                li.addClass(settings.classes.highlightedToken);
            }
        })
        .mouseout(function (event) {
            var li = get_element_from_event(event, "li");
            if(li && selected_token !== this) {
                li.removeClass(settings.classes.highlightedToken);
            }
        })
        .mousedown(function (event) {
            // Stop user selecting text on tokens
            var li = get_element_from_event(event, "li");
            if(li){
                return false;
            }
        });


    // The list to store the dropdown items in
    var dropdown = $("<div>")
        .addClass(settings.classes.dropdown)
        .insertAfter(token_list)
        .hide();

    // The token holding the input box
    var input_token = $("<li />")
        .addClass(settings.classes.inputToken)
        .appendTo(token_list)
        .append(input_box);

    //
    //
    // Functions
    //


  //If more than two countries exist, select Everywhere, disable other options, and get rid of all of their inputs
  function verify_token_inputs() {
    var countries = $('.token-input-country').length;
    //more than one country
    if (countries > 1) {
        //delete all other tokens
        $('.token-input-city').each( function(i) {
           delete_token($(this));
        });
        $('.token-input-state').each( function(i) {
           delete_token($(this));
        });
        //disable everything else
        $('input[name="region_targeting"]').each(
            function(i) {
                if ($(this).val() != 'all') {
                    $(this).attr('disabled', true);
                }
                //Select "Everywhere"
                else {
                    $(this).click();
                }
        });
    }
    // turn all buttons back on
    else {
        $('input[name="region_targeting"]').each(
            function(i) {
                $(this).attr('disabled', false);
        });
    }

    // Only show countryNumDpdnt things that match the current number
    // of countries in the input
    var children = $('#geo_pred_ta').children().length;
    $('.countryNumDependent').hide();
    $('.countryNumDependent.' + children).show();
  }



    // Pre-populate list if items exist
    function init_list () {
        var li_data = settings.prePopulate.data;
        if(li_data && li_data.length) {
            for(var i in li_data) {
                var token_data = new $.TokenData(li_data[i], settings.prePopulate.type);
                var this_token = $("<li><p>"+ token_data.name+"</p> </li>")
                    .addClass(settings.classes.token);
                if (token_data.type == 'city') {
                    this_token.addClass('token-input-city')
                    .addClass(token_data.raw.countryCode);
                }
                else if (token_data.type == 'country') {
                    this_token.addClass('token-input-country');
                }
                    this_token.insertBefore(input_token);
                $("<span>&times;</span>")
                    .addClass(settings.classes.tokenDelete)
                    .appendTo(this_token)
                    .click(function () {
                        delete_token($(this).parent());
                        return false;
                    });
                $.data(this_token.get(0), "tokeninput", token_data);

                // Clear input box and make sure it keeps focus
                input_box
                    .val("")
                    .focus();

                // Don't show the help dropdown, they've got the idea
                hide_dropdown();

                // Save this token id
                token_data.input().appendTo( hidden_input );
            }
        }
        input_box.blur();
    }

    init_list();
    verify_token_inputs();

    function is_printable_character(keycode) {
        if((keycode >= 48 && keycode <= 90) ||      // 0-1a-z
           (keycode >= 96 && keycode <= 111) ||     // numpad 0-9 + - / * .
           (keycode >= 186 && keycode <= 192) ||    // ; = , - . / ^
           (keycode >= 219 && keycode <= 222)       // ( \ ) '
          ) {
              return true;
          } else {
              return false;
          }
    }

    // Get an element of a particular type from an event (click/mouseover etc)
    function get_element_from_event (event, element_type) {
        return $(event.target).closest(element_type);
    }

    // Inner function to a token to the list
    function insert_token(datas) {
      var value = datas.name;
      var token_type;
      var this_token = $("<li><p>"+ value +"</p> </li>");

      if (datas.type == 'city') {
          this_token.addClass('token-input-city')
          .addClass(datas.raw.countryCode);
      }/*
      else if (datas.type == 'state') {
          token_type = 'token-input-state';
      }*/
      else if (datas.type == 'country') {
          this_token.addClass('token-input-country');
      }
      this_token.addClass(settings.classes.token)
      .insertBefore(input_token);

      // The 'delete token' button
      $("<span>x</span>")
          .addClass(settings.classes.tokenDelete)
          .appendTo(this_token)
          .click(function () {
              delete_token($(this).parent());
              return false;
          });
      $.data(this_token.get(0), "tokeninput", datas);
      return this_token;
    }

    // Add a token to the token list based on user input
    function add_token(item) {
        //Make sure token stuff is okay before adding a new one
        verify_token_inputs();
        var li_data = $.data(item.get(0), "tokeninput");
        var this_token = insert_token(li_data);
        var callback = settings.onAdd;

        // Clear input box and make sure it keeps focus
        input_box
            .val("")
            .focus();

        // Don't show the help dropdown, they've got the idea
        hide_dropdown();

        //XXX IMPORTANT XXX
        //order for id_string should be:
        // [country], region], city]
        // so US is US, California is US,CA and San Francisco is US,CA,SF (or some something like that)
        // This is because the django forms are going to take this id, split it on ',' and then assign
        // the first value as country_name, 2nd as region_name, and 3rd as city_name
        li_data.input().appendTo(hidden_input);

        token_count++;
        //Strictly increasing number so we can name the hidden inputs
        token_id++;

        if(settings.tokenLimit !== null && token_count >= settings.tokenLimit) {
            input_box.hide();
            hide_dropdown();
        }

        // Execute the onAdd callback if defined
        if($.isFunction(callback)) {
            callback(li_data.id);
        }
        //make sure token stuff is okay after adding a new one
        verify_token_inputs();
    }

    // Select a token in the token list
    function select_token (token) {
        token.addClass(settings.classes.selectedToken);
        selected_token = token.get(0);

        // Hide input box
        input_box.val("");

        // Hide dropdown if it is visible (eg if we clicked to select token)
        hide_dropdown();
    }

    // Deselect a token in the token list
    function deselect_token (token, position) {
        token.removeClass(settings.classes.selectedToken);
        selected_token = null;

        if(position == POSITION.BEFORE) {
            input_token.insertBefore(token);
        } else if(position == POSITION.AFTER) {
            input_token.insertAfter(token);
        } else {
            input_token.appendTo(token_list);
        }

        // Show the input box and give it focus again
        input_box.focus();
    }

    // Toggle selection of a token in the token list
    function toggle_select_token (token) {
        if(selected_token == token.get(0)) {
            deselect_token(token, POSITION.END);
        } else {
            if(selected_token) {
                deselect_token($(selected_token), POSITION.END);
            }
            select_token(token);
        }
    }

    // Delete a token from the token list
    function delete_token (token) {
        // Remove the id from the saved list
        var token_data = $.data(token.get(0), "tokeninput");
        var callback = settings.onDelete;
        // Delete the token
        token.remove();
        selected_token = null;
        //TODO delete the hidden field wooo
        // Show the input box and give it focus again
        input_box.focus();
        // Delete this token's id from hidden input
        if (token_data === undefined) {
            return;
        }
        var r_id = token_data.id.replace(/ /gi, '_');
        var r_nme = token_data.name.replace(/ /gi, '_');
        $('#'+ r_id).remove();
        $('#'+ r_nme).remove();

        if (token_data.type == 'country') {
            $('li.'+token_data.id+'.token-input-city').each( function(i) {
                    delete_token($(this));
                });
        }

        token_count--;

        if ($('.token-input-country').length === 0) {
            $('#advertiser-LocationSpec-all').click();
        }

        if (settings.tokenLimit !== null) {
            input_box
                .show()
                .val("")
                .focus();
        }


        // Execute the onDelete callback if defined
        if($.isFunction(callback)) {
          callback(token_data.id);
        }
        //verify inputs after token has been removed
        verify_token_inputs();
    }

    // Hide and clear the results dropdown
    function hide_dropdown () {
        dropdown.hide().empty();
        selected_dropdown_item = null;
    }

    function show_dropdown_searching () {
        dropdown
            .html("<p>"+settings.searchingText+"</p>")
            .show();
    }

    function show_dropdown_hint () {
        dropdown
            .html("<p>"+settings.hintText+"</p>")
            .show();
    }

    // Highlight the query part of the search term
	function highlight_term(value, term) {
        var ret_val = value.replace(new RegExp("(?![^&;]+;)(?!<[^<>]*)(" + term + ")(?![^<>]*>)(?![^&;]+;)", "gi"), "<b>$1</b>");
		return ret_val;
	}

    var slide_state = false;
    // Populate the results dropdown with some results
    function populate_dropdown (query, results) {
        var type = results.type;
        results = results.data;
        if(results && results.length) {
            var drop_clone = dropdown.clone();
            drop_clone.empty();
            var dropdown_ul = $("<ul>")
                .appendTo(drop_clone)
                .mouseover(function (event) {
                    select_dropdown_item(get_element_from_event(event, "li"));
                })
                .mousedown(function (event) {
                    add_token(get_element_from_event(event, "li"));
                    return false;
                });
            if ( !slide_state ) {
                dropdown_ul.hide();
            }
            var name;
            for(var i in results) {
                if (results.hasOwnProperty(i)) {
                    var tokenData = new $.TokenData(results[i],type);
                    var this_li = $("<li>"+highlight_term(tokenData.name, query)+"</li>")
                                      .appendTo(dropdown_ul);
                    if(i%2) {
                        this_li.addClass(settings.classes.dropdownItem);
                    } else {
                        this_li.addClass(settings.classes.dropdownItem2);
                    }
                    //JSLint doesn't like this, but needs to be == because '0' == 0 evals to true, but '0' === 0 does NOT
                    if(i == 0) {
                        select_dropdown_item(this_li);
                    }
                    $.data(this_li.get(0), "tokeninput", tokenData);
                }
            }
            dropdown.replaceWith(drop_clone);
            dropdown = drop_clone;
            dropdown.show();
            if (!slide_state) {
                slide_state = true;
                dropdown_ul.slideDown("fast");
            }

        } else {
            slide_state = false;
            dropdown
                .html("<p>"+settings.noResultsText+"</p>")
                .show();
        }
    }

    // Highlight an item in the results dropdown
    function select_dropdown_item (item) {
        if(item) {
            if(selected_dropdown_item) {
                deselect_dropdown_item($(selected_dropdown_item));
            }

            item.addClass(settings.classes.selectedDropdownItem);
            selected_dropdown_item = item.get(0);
        }
    }

    // Remove highlighting from an item in the results dropdown
    function deselect_dropdown_item (item) {
        item.removeClass(settings.classes.selectedDropdownItem);
        selected_dropdown_item = null;
    }

    // Do a search and show the "searching" dropdown if the input is longer
    // than settings.minChars
    function do_search(immediate) {
        var query = input_box.val().toLowerCase();

        if (query && query.length) {
            if(selected_token) {
                deselect_token($(selected_token), POSITION.AFTER);
            }
            if (query.length >= settings.minChars) {
                show_dropdown_searching();
                if (immediate) {
                    run_search(query);
                } else {
                    clearTimeout(timeout);
                    timeout = setTimeout(function(){run_search(query);}, settings.searchDelay);
                }
            } else if (query.length > 0) {
                show_dropdown_hint();
            }
            else {
                hide_dropdown();
            }
        }
    }

    // Do the actual search
    function run_search(query) {
        //Don't run with the query given, run with what's actually in the search box
        query = input_box.val().toLowerCase();
        var cached_results = cache.get(query);
        if(cached_results) {
            var pop = {type:'country', data:cached_results};
            populate_dropdown(query, pop);
        } else {
			var queryStringDelimiter = settings.url.indexOf("?") < 0 ? "?" : "&";
			var callback = function(results) {
              if($.isFunction(settings.onResult)) {
                  results = settings.onResult.call(this, results);
              }
              cache.add(query, settings.jsonContainer ? results[settings.jsonContainer] : results);
              var pop = {type: settings.type, data:results.geonames};
              populate_dropdown(query, pop);
            };

            if(settings.method == "POST") {
                $.post(settings.url + queryStringDelimiter + settings.queryParam + "=" + encodeURIComponent(query), {}, callback, settings.contentType);
            } else {
                var q_url = settings.url + queryStringDelimiter + settings.queryParam + "=" + encodeURIComponent(query);
                if (settings.featureClass !== null) {
                    q_url += '&featureClass=' + encodeURIComponent(settings.featureClass);
                }
                if (settings.featureCode !== null) {
                    q_url += "&featureCode=" + encodeURIComponent(settings.featureCode);
                }
                q_url += '&country=';
                if ($('input[name="geo_predicates"]').val() !== undefined) {
                   q_url += encodeURIComponent($('input[name="geo_predicates"]').val());
                }
                else {
                    q_url += encodeURIComponent(settings.country);
                }
                q_url += '&maxRows=' + settings.maxRows;
                $.get(q_url, {}, callback, settings.contentType);
            }
       }
    }
};

// Really basic cache for the results
$.TokenList.Cache = function (options) {
    var settings = $.extend({
        max_size: 50,
        matchContains: true
    }, options);

    function matchSubset( s, sub ) {
        if ( !options.matchCase ) {
            s = s.toLowerCase();
        }
        var i = s.indexOf( sub );
        if ( i == -1 ) {
            return false;
        }
        return i === 0 || options.matchContains;
    }


    var data = {};
    var size = 0;

    var flush = function () {
        data = {};
        size = 0;
    };

    function res_sort( query ) {
        function actual_sort( a, b ) {
            return q_dist( query, a.value ) - q_dist( query, b.value );
        }
        return actual_sort;
    }

    function q_dist( query, value ) {
        return value.length - query.length;
    }


    function get(q) {
        if (!options.cacheLength || !size) {
            return null;
        }
        if ( !options.url && settings.matchContains ){
           var csub = [];
           for ( var k in data ) {
               if( k.length > 0 ) {
                   var c = data[k];
                   $.each( c, function( i, x ) {
                      if (matchSubset( x.value, q ) ) {
                          var add = true;
                          for( var idx in csub ) {
                              var dat = csub[idx];
                              if ( x.result == dat.result ) {
                                  add = false;
                                  break;
                              }
                          }
                          if (add) {
                            csub.push(x);
                            }
                        }
                    });
               }
           }
           return csub.sort(res_sort(q));
        }
        else if( data[q] ) {
            return data[q];
        }
        else if (settings.matchSubset) {
            for (var i = q.length - 1; i >= 1; i--) {
                var c = data[ q.substr( 0, i ) ];
                if (c) {
                    var csub = [];
                    $.each( c, function( i, x ) {
                        if( matchSubset( x.value, q ) ){
                            csub[csub.length] = x;
                        }
                    });
                    return csub;
                }
            }
        }
        return null;
    }

    function populate() {
        if (!options.data ) {return false;}
        var stMatchSets = {},
            nullData = 0;

        if (!options.url) {options.cacheLength = 1;}

        stMatchSets[""] = [];

        for (var i = 0, ol = options.data.length; i < ol; i++ ) {
            var rawValue = options.data[i];
            rawValue = (typeof rawValue == "string" ) ? [rawValue] : rawValue;

            var values = options.formatMatch( rawValue, i+1, options.data.length );
            for (var j = 0; j < values.length; j++) {
                var value = values[j];
                if (value === false)
                    {continue;}
                var firstChar = value.charAt( 0 ).toLowerCase();
                if (!stMatchSets[ firstChar ] )
                    {stMatchSets[ firstChar ] = [];}
                var row = {
                     value: value,
                     data: rawValue,
                     result: options.formatResult && options.formatResult( rawValue ) || value
                 };
                 stMatchSets[ firstChar ].push( row );
                 if ( nullData++ < options.max ) {
                     stMatchSets[""].push( row );
                 }
            }
        }
        $.each( stMatchSets, function( i, value ) {
            options.cacheLength++;
            add( i, value );
        });
    }
    setTimeout(populate, 25);




    function add(query, results) {
        if(size > settings.max_size) {
            flush();
        }

        if(!data[query]) {
            size++;
        }
        data[query] = results;
    }

    return {
        flush: flush,
        get: get,
        populate: populate,
        add: add
    };


//    this.get = function (query) {
//        return data[query];
//    };
};

})(jQuery);

