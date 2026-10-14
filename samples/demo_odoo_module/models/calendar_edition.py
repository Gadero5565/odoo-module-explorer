from odoo import api, fields, models


class CalendarEdition(models.Model):
    _name = "demo.calendar.edition"
    _description = "Calendar Edition"

    name = fields.Char(required=True)
    year = fields.Integer()
    day_ids = fields.One2many("demo.calendar.day", "edition_id")
    day_count = fields.Integer(compute="_compute_day_count")

    @api.depends("day_ids")
    def _compute_day_count(self):
        for edition in self:
            edition.day_count = len(edition.day_ids)

    def action_publish(self):
        for edition in self:
            edition.write({"name": edition.name + " (published)"})
