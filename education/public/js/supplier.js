frappe.ui.form.on('Supplier', {
  refresh(frm) {
    console.log('Works')
    frm.set_query('default_bank_account', function () {
      return {
        filters: {
          party: frm.doc.name,
          party_type: 'Supplier',
          is_company_account: 0,
        },
      }
    })
  },
})
