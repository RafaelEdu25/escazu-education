frappe.ui.form.on('Room', {
    refresh: function(frm) {
        if (!frm.is_new()) {
            frm.add_custom_button(__('Ver Recursos del Aula'), function() {
                frappe.set_route('List', 'Physical Resource', { room: frm.doc.name });
            }, __('Inventario'));

            frm.add_custom_button(__('Agregar Recurso'), function() {
                let d = new frappe.ui.Dialog({
                    title: __('Agregar Recurso a {0}', [frm.doc.name]),
                    fields: [
                        { fieldname: 'resource_code', fieldtype: 'Data', label: 'Código', reqd: 1 },
                        { fieldname: 'resource_name', fieldtype: 'Data', label: 'Nombre del Recurso', reqd: 1 },
                        { fieldname: 'resource_type', fieldtype: 'Select', label: 'Tipo', options: 'Computadora\nProyector\nPizarra Digital\nMobiliario\nHerramienta\nOtro', reqd: 1 },
                        { fieldname: 'serial_no', fieldtype: 'Data', label: 'Número de Serie' },
                        { fieldname: 'is_fixed', fieldtype: 'Check', label: 'Es Fijo', default: 1 }
                    ],
                    primary_action_label: __('Guardar Recurso'),
                    primary_action: function(values) {
                        values.room = frm.doc.name;
                        values.status = 'Disponible';
                        frappe.call({
                            method: 'frappe.client.insert',
                            args: {
                                doc: Object.assign({ doctype: 'Physical Resource' }, values)
                            },
                            callback: function(r) {
                                if (!r.exc) {
                                    frappe.show_alert({ message: __('Recurso agregado'), indicator: 'green' });
                                    d.hide();
                                    frm.events.refresh_indicators(frm);
                                }
                            }
                        });
                    }
                });
                d.show();
            }, __('Inventario'));
        }

        frm.events.refresh_indicators(frm);
    },

    refresh_indicators: function(frm) {
        if (!frm.is_new()) {
            frappe.client.get_count('Physical Resource', { filters: { room: frm.doc.name, status: 'Disponible' } })
                .then(r => {
                    if (r.message !== undefined) {
                        frm.dashboard.add_indicator(__('Recursos disponibles: {0}', [r.message]), 'green');
                    }
                });

            frappe.client.get_count('Physical Resource', { filters: { room: frm.doc.name, status: 'En Mantenimiento' } })
                .then(r => {
                    if (r.message > 0) {
                        frm.dashboard.add_indicator(__('En mantenimiento: {0}', [r.message]), 'orange');
                    }
                });
        }
    },

    status: function(frm) {
        if (frm.doc.status !== 'Disponible') {
            frappe.db.get_count('Physical Resource', { filters: { room: frm.doc.name, status: 'Disponible' } })
                .then(count => {
                    if (count > 0) {
                        frappe.msgprint({
                            message: __('Hay {0} recursos marcados como disponibles en esta aula. Cambiar el estado del aula a {1} no cambia automáticamente el estado de los recursos. Se sugiere revisar el inventario.', [count, frm.doc.status]),
                            indicator: 'orange'
                        });
                    }
                });
        }
    }
});
