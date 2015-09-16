# -*- coding: utf-8 -*-
##############################################################################
#
#    OpenERP, Open Source Management Solution
<<<<<<< HEAD
#    Copyright (C) 2004-2013 Tiny SPRL (<http://tiny.be>).
#
#    This program is free software: you can redistribute it and/or modify
#    it under the terms of the GNU Affero General Public License as
#    published by the Free Software Foundation, either version 3 of the
#    License, or (at your option) any later version.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU Affero General Public License for more details.
#
#    You should have received a copy of the GNU Affero General Public License
#    along with this program.  If not, see <http://www.gnu.org/licenses/>.
#
##############################################################################

from openerp.osv import fields, osv

from datetime import datetime
from dateutil.relativedelta import relativedelta
from openerp import netsvc, SUPERUSER_ID
from openerp.tools.translate import _

import time
import pytz

class purchase_order(osv.osv):
    """
        Add new field Purchase Order
    """
    _name = 'purchase.order'
    _inherit = 'purchase.order'
    _description = 'KDERP Purchase Order'

    _columns = {
                'source_location_id':fields.many2one('stock.location','From Stock', ondelete='restrict', states={'done':[('readonly',True)], 'cancel':[('readonly',True)]})
                }
    
    def action_create_picking(self, cr, uid, ids, context = {}):
        picking_id = self.action_picking_create(cr, uid, ids, context)
        return picking_id    
    
    def action_cancel(self, cr, uid, ids, context=None):
        res = super(purchase_order, self).action_cancel(cr, uid, ids, context)
        wf_service = netsvc.LocalService("workflow")
        for po in self.browse(cr, uid, ids):
            for sp in po.picking_ids:
                if sp.state!='cancel':
                    wf_service.trg_validate(uid, 'stock.picking', sp.id, 'button_cancel', cr)
        return res
        
    def action_draft_to_final_quotation(self, cr, uid, ids, context=None):
        if not context:
            context = {}
        todo = []
        period_obj = self.pool.get('account.period')
        picking_ids = []
        for po in self.browse(cr, uid, ids, context=context):
            if not po.order_line:
                raise osv.except_osv(_('Error!'),_('You cannot confirm a purchase order without any purchase order line.'))
            for line in po.order_line:
                if line.state=='draft':
                    todo.append(line.id)

            period_id = po.period_id and po.period_id.id or False
            if not period_id:
                period_ids = period_obj.find(cr, uid, po.date_order, context)
                period_id = period_ids and period_ids[0] or False
            self.write(cr, uid, [po.id], {'state' : 'waiting_for_roa', 'period_id':period_id,'validator' : uid})                        
            
            sp_exists = False
            for sp in po.picking_ids:
                if sp.state!='cancel':
                    sp_exists = True
                    break
            if not sp_exists:
                picking_ids = self.action_create_picking(cr, uid, [po.id], context)
                
        self.pool.get('purchase.order.line').action_confirm(cr, uid, todo, context)
        return picking_ids
    
    def act_assign_move_picking(self, cr, uid, ids, context = {}):
        todo_moves = []
        stock_move = self.pool.get('stock.move')
        wf_service = netsvc.LocalService("workflow")
        self.write(cr, uid, ids, {'state' : 'waiting_for_delivery'}) 
        for po in self.browse(cr, uid, ids, context):
            for sp in po.picking_ids:
                if sp.state<>'cancel':
                    for sm in sp.move_lines:
                        todo_moves.append(sm.id)
                    wf_service.trg_validate(uid, 'stock.picking', sp.id, 'button_confirm', cr)
        stock_move.force_assign(cr, uid, todo_moves)               
        return ids
    
    def action_receive_picking(self, cr, uid, ids, context = {}):
        stock_move = self.pool.get('stock.move')                
        for po in self.browse(cr, uid, ids, context):
            for sp in po.picking_ids:
                todo_moves = []
                for sm in sp.move_lines:
                    todo_moves.append(sm.id)
                stock_move.action_done(cr, uid, todo_moves)                
        self.write(cr, uid, ids, {'state' : 'waiting_for_payment'})
        return ids
    
    #Stock Picking and MoveArea
    def date_to_datetime(self, cr, uid, userdate, context=None):
        """ Convert date values expressed in user's timezone to
        server-side UTC timestamp, assuming a default arbitrary
        time of 12:00 AM - because a time is needed.
    
        :param str userdate: date string in in user time zone
        :return: UTC datetime string for server-side use
        """
        from openerp.tools import DEFAULT_SERVER_DATE_FORMAT, DEFAULT_SERVER_DATETIME_FORMAT, DATETIME_FORMATS_MAP
        # TODO: move to fields.datetime in server after 7.0
        user_date = datetime.strptime(userdate, DEFAULT_SERVER_DATE_FORMAT)
        if context and context.get('tz'):
            tz_name = context['tz']
        else:
            tz_name = self.pool.get('res.users').read(cr, SUPERUSER_ID, uid, ['tz'])['tz']
        if tz_name:
            utc = pytz.timezone('UTC')
            context_tz = pytz.timezone(tz_name)
            user_datetime = user_date + relativedelta(hours=12.0)
            local_timestamp = context_tz.localize(user_datetime, is_dst=False)
            user_datetime = local_timestamp.astimezone(utc)
            return user_datetime.strftime(DEFAULT_SERVER_DATETIME_FORMAT)
        return user_date.strftime(DEFAULT_SERVER_DATETIME_FORMAT)
    
    def _prepare_order_picking(self, cr, uid, order, context=None, type='in'):
        return {
            'name': self.pool.get('stock.picking').get_newcode(cr, uid, type, context),
            'origin': order.name,
            'date': self.date_to_datetime(cr, uid, order.date_order, context),
            'partner_id': order.partner_id.id,
            'invoice_state': 'none', 
            'type': 'in',
            'purchase_id': order.id,
            #'company_id': order.company_id.id,
            'move_lines' : [],
        }
    
    def _prepare_order_line_move(self, cr, uid, order, order_line, picking_id, context=None, type = type):
        price_unit = order_line.price_unit
#        if order.currency_id.id != order.company_id.currency_id.id:
            #we don't round the price_unit, as we may want to store the standard price with more digits than allowed by the currency
#            price_unit = self.pool.get('res.currency').compute(cr, uid, order.currency_id.id, order.company_id.currency_id.id, price_unit, round=False, context=context)
        error = ""
        if (not order_line.location_id and not order.source_location_id) or  (not order_line.location_dest_id and not order.location_id):             
                error = _("""Not Available From Stock or To Stock, could you please check""")
        if error:
            raise osv.except_osv(_("KDERP Warning"), error)
        
        return {
            'name': order_line.name or '',
            'product_id': order_line.product_id.id,
            'product_qty': order_line.product_qty,
            'product_uos_qty': order_line.product_qty,
            'product_uom': order_line.product_uom.id,
            'product_uos': order_line.product_uom.id,
            'date': self.date_to_datetime(cr, uid, order.date_order, context),
            #'date_expected': self.date_to_datetime(cr, uid, order_line.date_planned, context),
            'location_id': order_line.location_id.id if order_line.location_id else order.source_location_id.id,
            'location_dest_id': order_line.location_dest_id.id if order_line.location_dest_id else order.location_id.id,
            'picking_id': picking_id,
            'partner_id': order.partner_id.id,
            #'move_dest_id': order_line.move_dest_id.id,
            'state': 'draft',
            'type':'in',
            'purchase_line_id': order_line.id,
            #'company_id': order.company_id.id,
            'price_unit': price_unit,
            'source_move_code':order_line.move_code
        }     
    
    def _create_pickings(self, cr, uid, order, order_lines, picking_id=False, context=None):
        """Creates pickings and appropriate stock moves for given order lines, then
        confirms the moves, makes them available, and confirms the picking.

        If ``picking_id`` is provided, the stock moves will be added to it, otherwise
        a standard outgoing picking will be created to wrap the stock moves, as returned
        by :meth:`~._prepare_order_picking`.

        Modules that wish to customize the procurements or partition the stock moves over
        multiple stock pickings may override this method and call ``super()`` with
        different subsets of ``order_lines`` and/or preset ``picking_id`` values.

        :param browse_record order: purchase order to which the order lines belong
        :param list(browse_record) order_lines: purchase order line records for which picking
                                                and moves should be created.
        :param int picking_id: optional ID of a stock picking to which the created stock moves
                               will be added. A new picking will be created if omitted.
        :return: list of IDs of pickings used/created for the given order lines (usually just one)
        """
        type = 'in'
        if not picking_id:
            picking_id = self.pool.get('stock.picking').create(cr, uid, self._prepare_order_picking(cr, uid, order, context=context, type = type))
        todo_moves = []
        stock_move = self.pool.get('stock.move')
        wf_service = netsvc.LocalService("workflow")
        for order_line in order_lines:
            if not order_line.product_id:
                continue
            if order_line.product_id.type in ('product', 'consu'):
                move = stock_move.create(cr, uid, self._prepare_order_line_move(cr, uid, order, order_line, picking_id, context=context, type = type))
                #if order_line.move_dest_id and order_line.move_dest_id.state != 'done':
                #    order_line.move_dest_id.write({'location_id': order.location_id.id})
                todo_moves.append(move)
        stock_move.action_confirm(cr, uid, todo_moves)
        return [picking_id]

    def action_picking_create(self, cr, uid, ids, context=None):
        picking_ids = []
        for order in self.browse(cr, uid, ids):
            picking_ids.extend(self._create_pickings(cr, uid, order, order.order_line, None, context=context))

        # Must return one unique picking ID: the one to connect in the subflow of the purchase order.
        # In case of multiple (split) pickings, we should return the ID of the critical one, i.e. the
        # one that should trigger the advancement of the purchase workflow.
        # By default we will consider the first one as most important, but this behavior can be overridden.
        return picking_ids[0] if picking_ids else False
    
purchase_order()

class purchase_order_line(osv.osv):
    """
        Add new field link Purchase Order Line
    """
    _name = 'purchase.order.line'
    _inherit = 'purchase.order.line'
    _description = 'Purchase Order Line'
    
    _columns = {                
                'location_id':fields.many2one('stock.location', 'From Stock'),
                'location_dest_id':fields.many2one('stock.location', 'To Stock'),                
                }   
=======
#    Copyright (C) 2004-2010 Tiny SPRL (<http://tiny.be>).
#
#    This program is free software: you can redistribute it and/or modify
#    it under the terms of the GNU Affero General Public License as
#    published by the Free Software Foundation, either version 3 of the
#    License, or (at your option) any later version.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU Affero General Public License for more details.
#
#    You should have received a copy of the GNU Affero General Public License
#    along with this program.  If not, see <http://www.gnu.org/licenses/>.
#
##############################################################################

from openerp.osv import fields, osv

#

#
   
class purchase_order_line(osv.osv):
    _inherit = 'purchase.order.line'        
    
>>>>>>> refs/remotes/origin/master
