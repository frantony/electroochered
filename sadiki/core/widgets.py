# -*- coding: utf-8 -*-
import datetime
from django.forms.widgets import MultiWidget, DateInput, TextInput
from time import strftime
from django import forms
from django.conf import settings
from django.utils import simplejson
from django.utils.safestring import mark_safe

DEFAULT_WIDTH = 500
DEFAULT_HEIGHT = 300

DEFAULT_LAT = 61.401951
DEFAULT_LNG = 55.160478

class JqueryUIDateWidget(DateInput):

    def __init__(self, attrs=None, default_class='datepicker textInput', **kwargs):
        if not attrs:
            attrs = {'class': default_class}
        else:
            if 'class' not in attrs:
                attrs.update({'class': default_class})
        super(JqueryUIDateWidget, self).__init__(attrs, kwargs)

    def render(self, name, value, *args, **kwargs):
        js = '''
        <script type="text/javascript">
        //<![CDATA[
            $(function(){{
            var datepicker_conf = {{maxDate: new Date(), dateFormat: '{format:>s}'}};
                $("#id_{name:>s}").datepicker(datepicker_conf);
            }});
        //]]>
        </script> '''.format(name=name, format=settings.JS_DATE_FORMAT)
        html = super(JqueryUIDateWidget, self).render(name, value, *args, **kwargs)
        return mark_safe(html + js)

    class Media:
        js = (
            "js/jqueryuidate.js",
            )

class JqueryUIFutureDateWidget(JqueryUIDateWidget):

    def render(self, name, value, *args, **kwargs):
        js = '''
        <script type="text/javascript">
        //<![CDATA[
            $(function(){{
                var datepicker_conf = {{minDate: new Date(), dateFormat: '{format:>s}'}};
                    $("#id_{name:>s}").datepicker(datepicker_conf);
                }});
        //]]>
        </script> '''.format(name=name, format=settings.JS_DATE_FORMAT)
        html = super(JqueryUIDateWidget, self).render(name, value, *args, **kwargs)
        return mark_safe(html + js)

    def __init__(self, attrs=None, default_class='datepicker_future', **kwargs):
        super(JqueryUIFutureDateWidget, self).__init__(
            attrs, default_class, **kwargs)

class JqSplitDateTimeWidget(MultiWidget):

    def __init__(self, attrs=None, date_format=None, time_format=None):
        date_class = attrs['date_class']
        time_class = attrs['time_class']
        del attrs['date_class']
        del attrs['time_class']

        time_attrs = attrs.copy()
        time_attrs['class'] = time_class
        time_attrs['size'] = 2
        date_attrs = attrs.copy()
        date_attrs['class'] = date_class

        attrs['class'] = 'datetimepicker'

        widgets = (DateInput(attrs=date_attrs, format=date_format),
                   TextInput(attrs=time_attrs), TextInput(attrs=time_attrs))

        super(JqSplitDateTimeWidget, self).__init__(widgets, attrs)

    def decompress(self, value):
        if value:
            d = strftime(settings.DATE_INPUT_FORMATS[0], value.timetuple())
            hour = strftime("%I", value.timetuple())
            minute = strftime("%M", value.timetuple())
            return d, hour, minute
        else:
            return None, None, None

    def format_output(self, rendered_widgets):
        """
        Given a list of rendered widgets (as strings), it inserts an HTML
        linebreak between them.

        Returns a Unicode string representing the HTML for the whole lot.
        """
        return u"Дата: %s<br/>Время: %s:%s" % (rendered_widgets[0], rendered_widgets[1],
                                                rendered_widgets[2])

    def render(self, name, value, *args, **kwargs):
        js = '''
        <script type="text/javascript">
        //<![CDATA[
            $(function(){{
                var datepicker_conf = {{maxDate: new Date(), dateFormat: '{format:>s}'}};
                    $("#id_{name:>s}_0").datepicker(datepicker_conf);
                }});
        //]]>
        </script> '''.format(name=name, format=settings.JS_DATE_FORMAT)
        html = super(JqSplitDateTimeWidget, self).render(name, value, *args, **kwargs)
        return mark_safe(html + js)

    class Media:
        js = ("js/jqueryuidate.js",)


class YearChoiceDateWigdet(forms.Select):

    def render(self, name, value, **kwds):
        if type(value) is datetime.date:
            value = '%s-01-01' % value.year
        return super(YearChoiceDateWigdet, self).render(name, value, **kwds)


class BooleanNextYearWidget(forms.CheckboxInput):

    def render(self, name, value, **kwds):
        value = not bool(value)
        return super(BooleanNextYearWidget, self).render(name, value, **kwds)
    
class AreaWidget(forms.Select):

    def render(self, name, value, **kwds):
        if value:
            value = value[0]
        else:
            value = u''
        return super(AreaWidget, self).render(name, value, **kwds)


class SelectMultipleJS(forms.SelectMultiple):
    class Media:
        js = (
            '%s/js/libs/jquery.bsmselect.js' % settings.STATIC_URL,
            '%s/js/libs/jquery.bsmselect.compatibility.js' % settings.STATIC_URL,
        )
        css = {
            'all': ('%s/css/plugins/jquery.bsmselect.css' % settings.STATIC_URL,),
        }

    def render(self, name, *args, **kwds):
        output = super(SelectMultipleJS, self).render(name, *args, **kwds)
        try:
            js = u"""
            <script type="text/javascript">
            //<![CDATA[
            $(function(){
                try {
                    $('#id_%s').bsmSelect({removeLabel: 'Удалить', title: '------'});
                } catch(err) {if (console) {console.log(err);}}
            });
            //]]>
            </script>""" % name
        except KeyError:
            pass
        else:
            output = mark_safe(output + js)
        return output


class PrefSadiksJS(SelectMultipleJS):

    def render(self, name, *args, **kwargs):
        from sadiki.core.models import Sadik, Area
        output = super(PrefSadiksJS, self).render(name, *args, **kwargs)
        sadiks_for_areas = {}
        for area in Area.objects.all():
            sadiks_dict=[unicode(sadik.id) for sadik in area.sadik_set.filter(active_registration=True)]
            sadiks_for_areas.update({unicode(area.id): sadiks_dict})
        sadiks_for_areas.update({"": [unicode(sadik.id) for sadik in Sadik.objects.all()]})
        areas_name=self.attrs.get('areas_name') or 'areas'
#        TODO:как-нибудь переделать,чтобы работа с id_areas была нормальной
        js = u"""
            <script type="text/javascript">
                //<![CDATA[
                $(function(){
                    $("#id_%s").filterOn("#id_%s", %s);
                });
                //]]>
            </script>""" % (name, areas_name, simplejson.dumps(sadiks_for_areas))
        return mark_safe(output+js)
