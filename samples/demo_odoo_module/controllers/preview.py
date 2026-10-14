"""Simple demonstration of routes for the static analyzer."""

from odoo import http


class CalendarPreview(http.Controller):
    @http.route('/demo/calendar/preview', type='http', auth='user')
    def preview(self, **kwargs):
        return 'Demo calendar preview'
