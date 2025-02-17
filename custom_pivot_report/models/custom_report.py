# -*- coding: utf-8 -*-
#############################################################################
#
# Cybrosys Technologies Pvt. Ltd.
#
# Copyright (C) 2023-TODAY Cybrosys Technologies(<https://www.cybrosys.com>)
# Author: Sreerag PM(odoo@cybrosys.com)
#
# You can modify it under the terms of the GNU LESSER
# GENERAL PUBLIC LICENSE (LGPL v3), Version 3.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the
# GNU LESSER GENERAL PUBLIC LICENSE (LGPL v3) for more details.
#
# You should have received a copy of the GNU LESSER GENERAL PUBLIC LICENSE
# (LGPL v3) along with this program.
# If not, see <http://www.gnu.org/licenses/>.
#
#############################################################################
from odoo import api, fields, models, _


class CustomReport(models.Model):
    """
        Custom report model for creating pivot view and adding required
        fields for the model
        """
    _name = 'custom.report'
    _description = 'Custom Report'

    name = fields.Char(string='Name',
                       help="Name of the custom report.")
    model_id = fields.Many2one('ir.model',
                               string='Model', required=True,
                               domain="[('transient', '=', False),]",
                               ondelete='cascade',
                               help="Select the base model for the "
                                    "custom report.")
    fields_ids = fields.One2many('custom.report.fields', 'report_id',
                                 string='Fields', required=True,
                                 help="Custom fields associated with "
                                      "this report.")
    menu_id = fields.Many2one('ir.ui.menu',
                              string='Menu', required=True,
                              ondelete='cascade',
                              help="The menu where you want to create a "
                                   "new menu item.")
    menu_group_ids = fields.Many2many('res.groups',
                                      string='Menu Group',
                                      required=True, ondelete='cascade',
                                      help="Groups with access to this "
                                           "menu item.")
    view_type = fields.Selection([('pivot', 'Pivot'), ('graph', 'Graph')],
                                 string='View Type',
                                 help="Type of view for the custom report.")

    def unlink(self):
        """Customized unlink method to clean up related records."""
        for rec in self:
            # Searching the view.
            view = self.env['ir.ui.view'].search(
                [('custom_report', '=', str(rec.id) + '_' + rec.model_id.model +
                  '_' + rec.menu_id.complete_name)])
            # Search the action.
            action = self.env['ir.actions.act_window'].search(
                [('custom_report', '=',
                  str(rec.id) + '_' + 'pivot' + '_' + '_' + 'current',)])
            # Search the menu.
            menu = self.env['ir.ui.menu'].search(
                [('custom_report', '=', str(rec.id) + '_' +
                  rec.menu_id.complete_name + '_' + rec.model_id.model)])
            view.sudo().unlink()
            action.sudo().unlink()
            menu.sudo().unlink()
        return super().unlink()

    @api.constrains('menu_id', 'fields_ids', 'model_id', 'name',
                    'menu_group_ids')
    def _create_menu_id(self):
        """
        Customized constraint method to create or update menu, action, and view.
        """
        view_id = self.env['ir.ui.view'].search(
            [('custom_report', '=', str(self.id) + '_' + self.model_id.model +
              '_' + self.menu_id.complete_name)])
        arch_base = '''<pivot string="%s" sample="1">\n''' % self.name
        for rec in self.fields_ids:
            if rec.row:
                arch_base += '''
                <field name="%s" type="row" string="%s"/>\n''' % (
                    rec.custom_field_id.name, rec.label)
            elif rec.measure:
                arch_base += '''
                <field name="%s" type="measure" string="%s"/>\n''' % (
                    rec.custom_field_id.name, rec.label)
            else:
                arch_base += '''<field name="%s" string="%s" />\n''' % (
                    rec.custom_field_id.name, rec.label)

        arch_base += '''</pivot>\n'''
        view_value = {
            'name': _(self.name),
            'type': 'pivot',
            'custom_report': (
                    str(self.id) + '_' + self.model_id.model + '_' +
                    self.menu_id.complete_name),
            'model': self.model_id.model,
            'mode': 'primary',
            'active': True,
            'arch_base': arch_base,
            'groups_id': [(6, 0, [self.menu_group_ids.id])],
        }
        if not view_id:
            # Creating the view.
            view_obj = self.env['ir.ui.view'].create(view_value)
        else:
            view_id.sudo().write(view_value)
            view_obj = view_id
        value = {
            'type': 'ir.actions.act_window',
            'name': _(self.name),
            'res_model': self.model_id.model,
            'custom_report': str(
                self.id) + '_' + 'pivot' + '_' + '_' + 'current',
            'view_mode': 'pivot',
            'view_id': view_obj.id,
            'target': 'current',
        }
        action_id = self.env['ir.actions.act_window'].search(
            [('custom_report', '=',
              str(self.id) + '_' + 'pivot' + '_' + '_' + 'current')])
        if not action_id:
            # Creating the action.
            action = self.env['ir.actions.act_window'].create(value)
        else:
            action_id.sudo().write(value)
            action = action_id
        value = {
            'name': self.name,
            'complete_name': self.menu_id.complete_name + '/' + self.name,
            'action': 'ir.actions.act_window,%s' % action.id,
            'parent_id': self.menu_id.id,
            'custom_report': (
                    str(self.id) + '_' + self.menu_id.complete_name + '_' +
                    self.model_id.model),
            'groups_id': [(6, 0, [self.menu_group_ids.id])],
        }
        menu_id = self.env['ir.ui.menu'].search([('custom_report', '=',
                                                  str(self.id) + '_' +
                                                  self.menu_id.complete_name +
                                                  '_' + self.model_id.model)])
        if not menu_id:
            # Creating the menu.
            self.env['ir.ui.menu'].create(value)
        else:
            menu_id.sudo().write(value)
