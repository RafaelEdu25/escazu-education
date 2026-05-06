frappe.ui.form.on('Course Document', {
    // Autocompletar nombre desde archivo
    document_file(frm, cdt, cdn) {
        let row = locals[cdt][cdn];
        if (row.document_file && !row.document_name) {
            let filename = row.document_file.split('/').pop()
                .replace(/\.[^/.]+$/, '') // quitar extensión
                .replace(/_/g, ' ');
            frappe.model.set_value(cdt, cdn, 'document_name', filename);
        }
    },

    // RF-17: validar fila antes de cerrar
    form_render(frm, cdt, cdn) {
        // Interceptar el botón de cierre del modal
        setTimeout(() => {
            // Ocultar botones innecesarios
            $(frm.fields_dict.course_documents?.grid?.grid_form?.wrapper)
                .find('.grid-insert-row-below, .grid-insert-row, .grid-duplicate-row')
                .hide();

            // También en la barra del modal (Insert Below/Above/Duplicate)
            $('.grid-header-toolbar').find(
                'button[data-label="Insert Below"], button[data-label="Insert Above"], button[data-label="Duplicate"]'
            ).hide();

        }, 50);
    }
});