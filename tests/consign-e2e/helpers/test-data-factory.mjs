// Test data factory — creates uniquely named records for E2E tests
import { create, searchRead, safeUnlink, rpcCall, callButton, read, write } from './odoo-rpc.mjs';

const TS = () => Date.now();

/** Create a test partner */
export async function createPartner(page, suffix = '') {
  const name = `E2E-Partner-${TS()}${suffix ? '-' + suffix : ''}`;
  const ids = await create(page, 'res.partner', { name, email: `${name.toLowerCase().replace(/\s+/g, '')}@test.local` });
  return { id: ids[0] || ids, name, model: 'res.partner' };
}

/** Create a portal user (partner + res.users with group_portal) */
export async function createPortalUser(page, suffix = '') {
  const partner = await createPartner(page, `portal${suffix}`);
  const login = `e2e-portal-${TS()}${suffix}`;
  const userIds = await create(page, 'res.users', {
    name: partner.name,
    login,
    password: 'TestPortal1234',
    partner_id: partner.id,
    groups_id: [[4, await getGroupId(page, 'base.group_portal')]],
  });
  return { userId: userIds[0] || userIds, partnerId: partner.id, login, password: 'TestPortal1234', partnerName: partner.name };
}

/** Get ir.model.data ID for an XML ref */
async function getGroupId(page, xmlid) {
  const [module, name] = xmlid.split('.');
  const recs = await searchRead(page, 'ir.model.data', [['module', '=', module], ['name', '=', name]], ['res_id'], 1);
  return recs[0]?.res_id;
}

/** Create test products: 1 trigger + N items */
export async function createProducts(page, itemCount = 2, suffix = '') {
  const ts = TS();
  const trigger = await create(page, 'product.product', {
    name: `E2E-Trigger-${ts}${suffix}`,
    list_price: 1000,
    type: 'service',
    sale_ok: true,
  });
  const items = [];
  for (let i = 0; i < itemCount; i++) {
    const ids = await create(page, 'product.product', {
      name: `E2E-Item${String.fromCharCode(65 + i)}-${ts}${suffix}`,
      list_price: 500 - i * 100,
      type: 'service',
      sale_ok: true,
    });
    items.push(ids[0] || ids);
  }
  return {
    triggerId: trigger[0] || trigger,
    itemIds: items,
    allIds: [trigger[0] || trigger, ...items],
  };
}

/** Create a consign program with trigger products.
 *  trigger_product_ids is a related field (rule_ids.product_ids) and the base
 *  model's create() strips it for non-gift_card/ewallet types.  We must create
 *  a loyalty.rule with the product_ids instead. */
export async function createConsignProgram(page, triggerProductIds, suffix = '') {
  const ts = TS();
  const ids = await create(page, 'loyalty.program', {
    name: `E2E-ConsignProg-${ts}${suffix}`,
    program_type: 'consign',
  });
  const progId = ids[0] || ids;
  // Create a loyalty.rule with the trigger product_ids
  if (triggerProductIds.length) {
    await create(page, 'loyalty.rule', {
      program_id: progId,
      product_ids: triggerProductIds.map(id => [4, id]),
    });
  }
  return { id: progId, model: 'loyalty.program' };
}

/** Create and confirm a sale order */
export async function createAndConfirmSO(page, partnerId, lines) {
  // lines: [{product_id, product_uom_qty, price_unit?}]
  const soIds = await create(page, 'sale.order', { partner_id: partnerId });
  const soId = soIds[0] || soIds;

  for (const line of lines) {
    await create(page, 'sale.order.line', {
      order_id: soId,
      product_id: line.product_id,
      product_uom_qty: line.product_uom_qty || 1,
      ...(line.price_unit != null ? { price_unit: line.price_unit } : {}),
    });
  }

  // Confirm the SO
  await callButton(page, 'sale.order', 'action_confirm', [soId]);
  return { id: soId, model: 'sale.order' };
}

/** Find consign card by program + partner */
export async function findConsignCard(page, programId, partnerId) {
  const cards = await searchRead(
    page, 'loyalty.card',
    [['program_id', '=', programId], ['partner_id', '=', partnerId]],
    ['id', 'code', 'consign_total_remaining_qty', 'consign_total_remaining_value', 'consign_active_lines'],
    1,
  );
  return cards[0] || null;
}

/** Create a card directly via RPC (no SO) */
export async function createCardDirect(page, programId, partnerId) {
  const ids = await create(page, 'loyalty.card', {
    program_id: programId,
    partner_id: partnerId,
  });
  return { id: ids[0] || ids, model: 'loyalty.card' };
}

/** Add a consign line to a card */
export async function addConsignLine(page, cardId, productId, qty, unitPrice, productDesc) {
  return rpcCall(page, 'loyalty.card', 'consign_add_line', [
    [cardId], productId, qty, unitPrice, productDesc || false, false,
  ]);
}

/** Create a redemption and confirm it */
export async function createAndConfirmRedemption(page, cardId, redemptionLines) {
  // redemptionLines: [{consign_line_id, qty_redeemed}]
  const redIds = await create(page, 'loyalty.consign.redemption', {
    card_id: cardId,
    line_ids: redemptionLines.map(l => [0, 0, {
      consign_line_id: l.consign_line_id,
      qty_redeemed: l.qty_redeemed,
    }]),
  });
  const redId = redIds[0] || redIds;
  await callButton(page, 'loyalty.consign.redemption', 'action_done', [redId]);
  return { id: redId, model: 'loyalty.consign.redemption' };
}

/** Batch cleanup — unlink records in reverse order, ignoring errors */
export async function cleanup(page, records) {
  for (const rec of [...records].reverse()) {
    await safeUnlink(page, rec.model, Array.isArray(rec.id) ? rec.id : [rec.id]);
  }
}
