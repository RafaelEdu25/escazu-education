frappe.ui.form.on('Physical Resource', {
    refresh: function(frm) {
        if (!frm.is_new()) {
            frm.add_custom_button(__('Ver Reservas'), function() {
                frappe.set_route('List', 'Resource Booking', { physical_resource: frm.doc.name });
            }, __('Acciones'));

            frappe.client.get_count('Resource Booking', { filters: { physical_resource: frm.doc.name, status: 'Confirmada' } })
                .then(r => {
                    if (r.message && r.message > 0) {
                        frm.dashboard.add_indicator(__('Reservas activas: {0}', [r.message]), 'blue');
                    }
                });
        }

        if (frm.doc.status && frm.doc.status !== 'Disponible') {
            let color = 'orange';
            if (['Fuera de Servicio', 'Dado de Baja'].includes(frm.doc.status)) {
                color = 'red';
            }
            frm.dashboard.add_indicator(frm.doc.status, color);
        }
    },

    room: function(frm) {
        if (frm.doc.room) {
            frappe.db.get_value('Room', frm.doc.room, 'status', function(r) {
                if (r && r.status && r.status !== 'Disponible') {
                    frappe.msgprint({
                        message: __('El aula seleccionada tiene estado distinto de Disponible. ¿Desea continuar de todas formas?'),
                        indicator: 'orange'
                    });
                }
            });
        }
    }
});
