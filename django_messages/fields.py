"""
Based on http://www.djangosnippets.org/snippets/595/
by sopelkin
"""

from django import forms
from django.forms import widgets
from django.contrib.auth.models import User
from django.utils.translation import ugettext_lazy as _
from django.utils.html import conditional_escape
from django.utils.safestring import mark_safe
from django.utils.encoding import force_unicode

class CommaSeparatedUserInput(widgets.HiddenInput):

    def render(self, name, value, attrs=None):
        if value is None:
            value = ''
        elif isinstance(value, (list, tuple)):
            value = (', '.join([str(user.pk) for user in value]))
        return super(CommaSeparatedUserInput, self).render(name, value, attrs)

class CommaSeparatedUserField(forms.Field):
    widget = CommaSeparatedUserInput
    
    def __init__(self, *args, **kwargs):
        recipient_filter = kwargs.pop('recipient_filter', None)
        self._recipient_filter = recipient_filter
        super(CommaSeparatedUserField, self).__init__(*args, **kwargs)
        
    def clean(self, value):
        super(CommaSeparatedUserField, self).clean(value)
        if not value:
            return ''
        if isinstance(value, (list, tuple)):
            return value
        
        ids = set(value.split(','))
        ids_set = set([uid.strip() for uid in ids if uid.strip()])
        users = list(User.objects.filter(pk__in=ids_set))
        unknown_ids = ids_set ^ set([str(user.pk) for user in users])
        
        recipient_filter = self._recipient_filter
        invalid_users = []
        if recipient_filter is not None:
            for r in users:
                if recipient_filter(r) is False:
                    users.remove(r)
                    invalid_users.append(r.gk)
        
        if unknown_ids or invalid_users:
            incorrect = [str(uid) for uid in list(unknown_ids)+invalid_users]
            raise forms.ValidationError(u"The following user IDs are incorrect: %(users)s" % {'users': ', '.join(incorrect)})
        
        return users

class PlainTextWidget(widgets.HiddenInput):
    is_hidden = False

    def render(self, name, value, attrs=None):
        if value is None:
            value = ''
        value = conditional_escape(force_unicode(value))
        return mark_safe(u'<p>%s</p>' % value)+super(PlainTextWidget, self).render(name, value, attrs)

class PlainHTMLWidget(widgets.HiddenInput):
    is_hidden = False

    def render(self, name, value, attrs=None):
        if value is None:
            value = ''
        return conditional_escape(force_unicode(value))

class ReadOnlyField(forms.Field):
    required = False
    widget = PlainHTMLWidget
