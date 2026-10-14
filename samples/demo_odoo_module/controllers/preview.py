"""Simple demonstration of routes for the static analyzer."""

from odoo import http


class CalendarPreview(http.Controller):
    @http.route('/demo/calendar/preview', type='http', auth='user')
    def preview(self, **kwargs):
        return 'Demo calendar preview'

    @http.route('/demo/calendar/edit_view', type='http', auth='user')
    def edit_view(self, **kwargs):
        return 'Demo calendar edit_view'
