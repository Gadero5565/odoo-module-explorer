from odoo import fields, models


class CalendarDay(models.Model):
    _name = "demo.calendar.day"
    _description = "Calendar Day"

    name = fields.Char()
    edition_id = fields.Many2one("demo.calendar.edition", required=True)
    date = fields.Date()
