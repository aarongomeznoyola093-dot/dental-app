window.addEventListener("load", () => {
    
    async function fetchWithAuth(url, options = {}) {
        const token = sessionStorage.getItem('access_token');

        if (!token) {
            window.location.href = '/app/login.html';
            return Promise.reject(new Error("Token no encontrado"));
        }

        const headers = {
            ...options.headers,
            'Authorization': `Bearer ${token}`
        };

        const response = await fetch(url, { ...options, headers });

        if (response.status === 401) { 
            sessionStorage.removeItem('access_token');
            alert("Tu sesión ha expirado. Por favor, inicia sesión de nuevo.");
            window.location.href = '/app/login.html';
            return Promise.reject(new Error("Token inválido o expirado"));
        }

        return response;
    }

    const vistaPrincipal = document.getElementById('vistaPrincipal');
    const vistaHistorial = document.getElementById('vistaHistorial');
    const btnVolver = document.getElementById('btnVolver');
    const formPaciente = document.getElementById("formPaciente");
    const formPacienteTitulo = document.getElementById("formPacienteTitulo");
    const pacienteFormButton = formPaciente ? formPaciente.querySelector("button[type='submit']") : null;
    let idPacienteActual = null; 
    let historialPacienteActual = null;
    let listaCompletaPacientes = []; 

    function init() {
        configurarTodosLosFormularios();
        configurarManejadorDeEventosPrincipal();
        cargarDatosIniciales();
        configurarCalendario();
        cargarDashboard();
    }

    async function cargarDatosIniciales() {
        try {
            await cargarPacientes();
            await cargarTratamientos();
        } catch (error) {
            console.error("Error durante la carga inicial de datos:", error);
        }
    }

    function configurarTodosLosFormularios() {
        configurarFormularioPaciente();
        configurarFormularioCita();
        configurarFormularioTratamiento();
        configurarFormularioCitaTratamiento();
        configurarFormularioPago();
        configurarFormularioAbono();
    }

    function configurarManejadorDeEventosPrincipal() {
        if (btnVolver) {
            btnVolver.addEventListener('click', salirModoEdicion);
        }

        document.body.addEventListener('click', function(event) {
            const target = event.target;
            
            const filaPaciente = target.closest('.fila-clicable');
            if (filaPaciente) {
                cargarHistorialPaciente(filaPaciente.getAttribute('data-id'));
                return;
            }

            const actionMap = {
                '.btn-editar-paciente': iniciarModoEdicion,
                '.btn-eliminar-paciente': eliminarPaciente,
                '.btn-editar-tratamiento': iniciarEdicionTratamiento,
                '.btn-eliminar-tratamiento': eliminarTratamiento,
                '.btn-editar-cita': iniciarEdicionCita,
                '.btn-eliminar-cita': eliminarCita,
                
                '.btn-editar-pago': (button) => iniciarEdicionPago(button.getAttribute('data-id-pago'), button.getAttribute('data-id-cita')),
                '.btn-eliminar-pago': (button) => eliminarPago(button.getAttribute('data-id-pago'), button.getAttribute('data-id-cita')),
                '.btn-editar-abono': (button) => iniciarEdicionAbono(button.getAttribute('data-id-abono')),
                '.btn-eliminar-abono': (button) => eliminarAbono(button.getAttribute('data-id-abono'))
            };

            for (const selector in actionMap) {
                const button = target.closest(selector);
                if (button) {
                    if (selector.includes('-pago') || selector.includes('-abono')) {
                        actionMap[selector](button); 
                    } else {
                        actionMap[selector](button.getAttribute('data-id')); 
                    }
                    return; 
                }
            }
        });

        const btnReporte = document.getElementById("btnGenerarReporte");
        if (btnReporte) {
            btnReporte.addEventListener("click", async () => {
                const fecha = new Date().toLocaleDateString('es-ES', { month: 'long', year: 'numeric' });
                
                const valPacientes = document.getElementById("dashPacientes") ? document.getElementById("dashPacientes").textContent : "0";
                const valCitas = document.getElementById("dashCitas") ? document.getElementById("dashCitas").textContent : "0";
                const valIngresos = document.getElementById("dashIngresos") ? document.getElementById("dashIngresos").textContent : "$0.00";

                const ventana = window.open('', 'PRINT', 'height=600,width=800');
                ventana.document.write(`
                    <html>
                    <head>
                        <title>Reporte Mensual - ${fecha}</title>
                        <style>
                            body { font-family: sans-serif; padding: 20px; }
                            h1 { color: #6a5acd; text-align: center; }
                            table { width: 100%; border-collapse: collapse; margin-top: 20px; }
                            th, td { border: 1px solid #ddd; padding: 8px; text-align: left; }
                            th { background-color: #f2f2f2; }
                            .total { font-size: 1.5em; font-weight: bold; text-align: right; margin-top: 20px; }
                        </style>
                    </head>
                    <body>
                        <h1>Reporte Mensual: ${fecha}</h1>
                        <p><strong>Dental Criss</strong> - Dra. Sandra Gómez Osorio</p>
                        <hr>
                        <h3>Resumen de Actividad</h3>
                        <table>
                            <tr><th>Métrica</th><th>Valor</th></tr>
                            <tr><td>Pacientes Activos</td><td>${valPacientes}</td></tr>
                            <tr><td>Citas Atendidas</td><td>${valCitas}</td></tr>
                        </table>
                        <div class="total">
                            Ingresos Totales: ${valIngresos}
                        </div>
                        <br><br>
                        <p style="text-align: center; font-size: 0.8em; color: #777;">Generado automáticamente por el Sistema Dental Criss</p>
                    </body>
                    </html>
                `);
                ventana.document.close(); 
                ventana.focus();
                setTimeout(() => { ventana.print(); ventana.close(); }, 500);
            });
        }
    }

    async function cargarPacientes() {
        const container = document.getElementById("tablaPacientesContainer");
        if (!container) return;
        container.innerHTML = "<p>Cargando pacientes...</p>";

        try {
            
            const respuesta = await fetchWithAuth("/pacientes/");
            if (!respuesta.ok) throw new Error("Error del servidor");

            listaCompletaPacientes = await respuesta.json(); 
            renderizarTablaPacientes(listaCompletaPacientes);

            const inputBusqueda = document.getElementById("inputBusquedaPaciente");
            inputBusqueda.addEventListener("input", (e) => {
                const termino = e.target.value.toLowerCase().trim();
                const filtrados = listaCompletaPacientes.filter(p => {
                    const nombreCompleto = `${p.nombre} ${p.apellido_pat} ${p.apellido_mat}`.toLowerCase();
                    return nombreCompleto.includes(termino);
                });
                renderizarTablaPacientes(filtrados);
            });

        } catch (error) {
            if (error.message.includes("Token")) return;
            container.innerHTML = "<p style='color:red;'>Error al cargar la lista de pacientes.</p>";
        }
    }

    function renderizarTablaPacientes(pacientes) {
        const container = document.getElementById("tablaPacientesContainer");
        if (pacientes.length === 0) {
            container.innerHTML = "<p>No se encontraron pacientes.</p>";
            return;
        }
        let tablaHtml = `<table><thead><tr><th>Nombre Completo</th><th>Edad</th><th>Teléfono</th><th>ID del Paciente</th></tr></thead><tbody>`;
        pacientes.forEach(p => {
            tablaHtml += `<tr class="fila-clicable" data-id="${p.id_paciente}" title="Haz clic para ver el historial">
                            <td>${p.nombre} ${p.apellido_pat || ''} ${p.apellido_mat || ''}</td>
                            <td>${p.edad}</td>
                            <td>${p.telefono}</td>
                            <td><code>${p.id_paciente}</code></td>
                          </tr>`;
        });
        container.innerHTML = tablaHtml + `</tbody></table>`;
    }

    async function cargarTratamientos() {
        const container = document.getElementById("tablaTratamientosContainer");
        if (!container) return;
        container.innerHTML = "<p>Cargando tratamientos...</p>";
        try {
            
            const respuesta = await fetchWithAuth("/tratamientos/");
            if (!respuesta.ok) throw new Error("Error del servidor");
            const tratamientos = await respuesta.json();
            if (tratamientos.length === 0) {
                container.innerHTML = "<p>No hay tratamientos registrados.</p>"; return;
            }
            let tablaHtml = `<table><thead><tr><th>Nombre</th><th>Categoría</th><th>Precio</th><th>Acciones</th></tr></thead><tbody>`;
            tratamientos.forEach(t => {
                tablaHtml += `<tr><td>${t.nombre}</td><td>${t.categoria}</td><td>$${t.precio}</td><td><button class="btn-accion btn-editar-tratamiento" data-id="${t.id_tratamiento}">✏️</button><button class="btn-accion btn-eliminar-tratamiento" data-id="${t.id_tratamiento}">🗑️</button><br><small><code>${t.id_tratamiento}</code></small></td></tr>`;
            });
            container.innerHTML = tablaHtml + `</tbody></table>`;
        } catch (error) {
            if (error.message.includes("Token")) return;
            container.innerHTML = "<p style='color:red;'>Error al cargar los tratamientos.</p>";
        }
    }
    
    async function cargarHistorialPaciente(id_paciente) {
        idPacienteActual = id_paciente;
        vistaPrincipal.style.display = 'none';
        vistaHistorial.style.display = 'block';
        const container = document.getElementById('historialContainer');
        container.innerHTML = '<p>Cargando historial...</p>';
        try {
            // RUTA CORREGIDA: Sin /api/v1
            const respuesta = await fetchWithAuth(`/pacientes/${id_paciente}/historial`);
            if (!respuesta.ok) throw new Error("Error del servidor");

            historialPacienteActual = await respuesta.json(); 
            container.innerHTML = generarHtmlHistorial(historialPacienteActual); 

        } catch (error) {
            historialPacienteActual = null;
            if (error.message.includes("Token")) return;
            container.innerHTML = "<p style='color:red;'>Error al cargar el historial.</p>"; 
        }
    }

    function generarHtmlHistorial(historial) {
        const p = historial.paciente;
        let fechaNacimientoFormateada = "No especificada";
        if (p.fecha_nacimiento && typeof p.fecha_nacimiento === 'string') {
            const partes = p.fecha_nacimiento.split('-');
            if (partes.length === 3) fechaNacimientoFormateada = `${partes[2]}/${partes[1]}/${partes[0]}`;
        }
        let html = `<button class="btn-accion btn-editar-paciente" data-id="${p.id_paciente}">✏️ Editar Paciente</button><button class="btn-accion btn-eliminar-paciente" data-id="${p.id_paciente}">🗑️ Eliminar Paciente</button><h2>Historial de ${p.nombre} ${p.apellido_pat}</h2><div style="background: #f4f4f4; padding: 15px; border-radius: 8px;"><p><strong>ID:</strong> <code>${p.id_paciente}</code></p><p><strong>Edad:</strong> ${p.edad} | <strong>Teléfono:</strong> ${p.telefono}</p><p><strong>Fecha de Nacimiento:</strong> ${fechaNacimientoFormateada}</p><p><strong>Enfermedades:</strong> ${p.enfermedades?.join(', ') || 'Ninguna'}</p><p><strong>Medicamentos:</strong> ${p.medicamentos?.join(', ') || 'Ninguno'}</p><p><strong>Alergias:</strong> ${p.alergias?.join(', ') || 'Ninguna'}</p></div><hr><h2>Citas y Procedimientos</h2>`;
        
        if (!historial.citas_detalladas || historial.citas_detalladas.length === 0) {
            html += '<p>No hay citas registradas.</p>';
        } else {
            historial.citas_detalladas.sort((a, b) => new Date(b.fecha_hora) - new Date(a.fecha_hora)).forEach(cita => {
                html += `<div style="border: 1px solid #ccc; padding: 10px; margin-bottom: 15px; border-radius: 8px;"><div><button class="btn-accion btn-editar-cita" data-id="${cita.id_cita}">✏️ Editar Cita</button><button class="btn-accion btn-eliminar-cita" data-id="${cita.id_cita}">🗑️ Eliminar Cita</button></div><h3>Cita del ${new Date(cita.fecha_hora).toLocaleString('es-ES')}</h3><p><strong>ID Cita:</strong> <code>${cita.id_cita}</code></p><p><strong>Motivo:</strong> ${cita.motivo} | <strong>Estado:</strong> ${cita.estado}</p><h4>Tratamientos en esta cita:</h4>`;
                
                if (cita.tratamientos?.length > 0) {
                    cita.tratamientos.forEach(t => { html += `<p style="margin-left: 20px;">- <strong>Obs:</strong> ${t.observaciones || 'S/O'} (<strong>Res:</strong> ${t.resultado || 'Pendiente'})</p>`; });
                } else { html += '<p style="margin-left: 20px;">Ningún tratamiento asignado.</p>'; }

                html += '<h4>Pagos de esta cita:</h4>';
                if (cita.pagos?.length > 0) {
                    html += '<table style="font-size: 0.9em; margin-left: 20px; width: 90%;"><thead><tr><th>Monto</th><th>Fecha</th><th>Método</th><th>ID Pago</th><th>Acciones</th></tr></thead><tbody>';
                    cita.pagos.forEach(pago => {
                        let fechaPagoFmt = "N/A";
                        if (pago.fecha_pago && typeof pago.fecha_pago === 'string') {
                            const partes = pago.fecha_pago.split('-'); 
                            if (partes.length === 3) fechaPagoFmt = `${partes[2]}/${partes[1]}/${partes[0]}`;
                        }
                        html += `<tr>
                                    <td>$${pago.monto || 'N/A'}</td>
                                    <td>${fechaPagoFmt}</td>
                                    <td>${pago.metodo_pago || 'N/A'}</td>
                                    <td><code>${pago.id_pago}</code></td>
                                    <td>
                                        <button class="btn-accion btn-editar-pago" data-id-pago="${pago.id_pago}" data-id-cita="${cita.id_cita}" title="Editar Pago">✏️</button>
                                        <button class="btn-accion btn-eliminar-pago" data-id-pago="${pago.id_pago}" data-id-cita="${cita.id_cita}" title="Eliminar Pago">🗑️</button>
                                    </td>
                                 </tr>`;
                    });
                    html += '</tbody></table>';
                } else {
                    html += '<p style="margin-left: 20px;">No hay pagos registrados para esta cita.</p>';
                }
                html += '</div>';
            });
        }

        html += '<hr><h2>Estado de Cuenta (Abonos)</h2>';
        if (historial.abonos?.length > 0) {
            html += '<table><thead><tr><th>Monto Abonado</th><th>Saldo Restante</th><th>Fecha</th><th>Estado</th><th>ID Abono</th><th>Acciones</th></tr></thead><tbody>';
            historial.abonos.forEach(abono => {
                let fechaAbonoFmt = "N/A";
                if (abono.fecha_abono && typeof abono.fecha_abono === 'string') {
                    const partes = abono.fecha_abono.split('-'); 
                    if (partes.length === 3) fechaAbonoFmt = `${partes[2]}/${partes[1]}/${partes[0]}`;
                }
                html += `<tr>
                            <td>$${abono.monto_abonado || '0'}</td>
                            <td>$${abono.saldo_restante || '0'}</td>
                            <td>${fechaAbonoFmt}</td>
                            <td>${abono.estado || 'N/A'}</td>
                            <td><code>${abono.id_abono}</code></td>
                            <td>
                                <button class="btn-accion btn-editar-abono" data-id-abono="${abono.id_abono}" title="Editar Abono">✏️</button>
                                <button class="btn-accion btn-eliminar-abono" data-id-abono="${abono.id_abono}" title="Eliminar Abono">🗑️</button>
                            </td>
                         </tr>`;
            });
            html += '</tbody></table>';
        } else {
            html += '<p>No hay abonos generales registrados para este paciente.</p>';
        }
        return html;
    }

    function salirModoEdicion() {
        idPacienteActual = null;
        vistaHistorial.style.display = 'none';
        vistaPrincipal.style.display = 'block';
        const forms = document.querySelectorAll('form');
        forms.forEach(form => {
            form.reset();
            form.removeAttribute("data-edit-id");
        });
        document.getElementById("formPacienteTitulo").textContent = "Gestión de Pacientes";
        document.getElementById("formCitaTitulo").textContent = "Registrar Cita";
        document.getElementById("formTratamientoTitulo").textContent = "Registrar Tratamiento";
        if(pacienteFormButton) pacienteFormButton.textContent = "Guardar Paciente";
        document.querySelector("#formCita button").textContent = "Guardar Cita";
        document.querySelector("#formTratamiento button").textContent = "Guardar Tratamiento";
    }

    async function iniciarModoEdicion(id_paciente) {
        try {
            
            const respuesta = await fetchWithAuth(`/pacientes/${id_paciente}/historial`);
            if (!respuesta.ok) throw new Error('No se pudo obtener la info del paciente.');
            const historial = await respuesta.json();
            const p = historial.paciente;
            formPaciente.querySelector("#nombre").value = p.nombre;
            formPaciente.querySelector("#apellidoPat").value = p.apellido_pat;
            formPaciente.querySelector("#apellidoMat").value = p.apellido_mat;
            formPaciente.querySelector("#fechaNacimiento").value = p.fecha_nacimiento;
            formPaciente.querySelector("#edad").value = p.edad;
            formPaciente.querySelector("#telefono").value = p.telefono;
            formPaciente.querySelector("#enfermedades").value = p.enfermedades?.join(", ") || "";
            formPaciente.querySelector("#medicamentos").value = p.medicamentos?.join(", ") || "";
            formPaciente.querySelector("#alergias").value = p.alergias?.join(", ") || "";
            formPaciente.setAttribute("data-edit-id", id_paciente);
            formPacienteTitulo.textContent = "Editando Paciente";
            pacienteFormButton.textContent = "Actualizar Paciente";
            vistaHistorial.style.display = 'none';
            vistaPrincipal.style.display = 'block';
            formPaciente.scrollIntoView({ behavior: 'smooth', block: 'start' });
        } catch (error) {
            if (error.message.includes("Token")) return;
            alert("Error al cargar datos para editar: " + error.message);
        }
    }

    async function eliminarPaciente(id_paciente) {
        if (!confirm("¿Seguro que quieres eliminar a este paciente y todos sus datos asociados?")) return;
        try {
            // RUTA CORREGIDA
            const respuesta = await fetchWithAuth(`/pacientes/${id_paciente}`, { method: 'DELETE' });
            if (!respuesta.ok) throw new Error((await respuesta.json()).detail || "Error del servidor");
            const resultado = await respuesta.json();
            alert(resultado.mensaje);
            setTimeout(() => {
                salirModoEdicion();
                cargarPacientes();
            }, 0);
        } catch (error) {
            if (error.message.includes("Token")) return;
            alert("Error al eliminar paciente: " + error.message);
        }
    }

    async function iniciarEdicionTratamiento(id_tratamiento) {
        try {
            
            const respuesta = await fetchWithAuth(`/tratamientos/${id_tratamiento}`);
            
            if (!respuesta.ok) throw new Error('No se pudo obtener la info del tratamiento.');
            const t = await respuesta.json();
            const form = document.getElementById("formTratamiento");
            form.querySelector("#nombreTratamiento").value = t.nombre;
            form.querySelector("#categoriaTratamiento").value = t.categoria;
            form.querySelector("#descripcionTratamiento").value = t.descripcion;
            form.querySelector("#precioTratamiento").value = t.precio;
            if (t.duracion_estimada) {
                const unidad = Object.keys(t.duracion_estimada)[0];
                const valor = t.duracion_estimada[unidad];
                form.querySelector("#duracionValor").value = valor;
                form.querySelector("#duracionUnidad").value = unidad;
            }
            form.setAttribute("data-edit-id", id_tratamiento);
            document.getElementById("formTratamientoTitulo").textContent = "Editando Tratamiento";
            form.querySelector("button[type='submit']").textContent = "Actualizar Tratamiento";
            form.scrollIntoView({ behavior: 'smooth' });
        } catch (error) {
            if (error.message.includes("Token")) return;
            alert("Error al cargar datos para editar: " + error.message);
        }
    }

    async function eliminarTratamiento(id_tratamiento) {
        if (!confirm("¿Seguro que quieres eliminar este tratamiento del catálogo?")) return;
        try {
            
            const respuesta = await fetchWithAuth(`/tratamientos/${id_tratamiento}`, { method: 'DELETE' });
            if (!respuesta.ok) throw new Error((await respuesta.json()).detail || "Error del servidor");
            const resultado = await respuesta.json();
            alert(resultado.mensaje);
            cargarTratamientos();
        } catch (error) {
            if (error.message.includes("Token")) return;
            alert("Error al eliminar tratamiento: " + error.message);
        }
    }

    async function iniciarEdicionCita(id_cita) {
        try {
            
            const respuesta = await fetchWithAuth(`/citas/${id_cita}`);
            if (!respuesta.ok) throw new Error('No se pudo obtener la info de la cita.');
            const c = await respuesta.json();
            const form = document.getElementById("formCita");
            form.querySelector("#idPacienteCita").value = c.id_paciente;
            form.querySelector("#fechaHoraCita").value = c.fecha_hora ? c.fecha_hora.slice(0, 16) : "";
            form.querySelector("#motivoCita").value = c.motivo;
            form.querySelector("#estadoCita").value = c.estado;
            form.setAttribute("data-edit-id", id_cita);
            document.getElementById("formCitaTitulo").textContent = "Editando Cita";
            form.querySelector("button[type='submit']").textContent = "Actualizar Cita";
            vistaHistorial.style.display = 'none';
            vistaPrincipal.style.display = 'block';
            form.scrollIntoView({ behavior: 'smooth' });
        } catch (error) {
            if (error.message.includes("Token")) return;
            alert("Error al cargar datos de la cita para editar: " + error.message);
        }
    }

    async function eliminarCita(id_cita) {
        if (!idPacienteActual) {
            alert("Error: No se pudo identificar al paciente de esta cita para eliminarla.");
            return;
        }
        if (!confirm("¿Seguro que quieres eliminar esta cita y sus datos asociados?")) return;
        try {
            
            const respuesta = await fetchWithAuth(`/citas/${id_cita}`, { 
                method: 'DELETE',
                headers: { "Content-Type": "application/json" },
                body: JSON.stringify({ id_paciente: idPacienteActual })
            });
            if (!respuesta.ok) throw new Error((await respuesta.json()).detail || "Error del servidor");
            const resultado = await respuesta.json();
            alert(resultado.mensaje);
            cargarHistorialPaciente(idPacienteActual);
        } catch (error) {
            if (error.message.includes("Token")) return;
            alert("Error al eliminar la cita: " + error.message);
        }
    }
function configurarFormularioPaciente() {
    if (!formPaciente) return;
    formPaciente.addEventListener("submit", async function(e) {
        e.preventDefault();
        const editId = formPaciente.getAttribute("data-edit-id");
        
        // ✅ Función corregida
        const textoALista = (texto) => {
            if (!texto || texto.trim() === "" || texto.toLowerCase() === "ninguna") {
                return [];
            }
            return texto.split(",").map(item => item.trim()).filter(Boolean);
        };
        
        const pacienteData = {
            nombre: document.getElementById("nombre").value,
            apellido_pat: document.getElementById("apellidoPat").value,
            apellido_mat: document.getElementById("apellidoMat").value,
            fecha_nacimiento: document.getElementById("fechaNacimiento").value,
            edad: parseInt(document.getElementById("edad").value),
            telefono: document.getElementById("telefono").value,
            enfermedades: textoALista(document.getElementById("enfermedades").value),
            medicamentos: textoALista(document.getElementById("medicamentos").value),
            alergias: textoALista(document.getElementById("alergias").value)
        };
        
        const url = editId ? `/pacientes/${editId}` : "/pacientes/";
        const method = editId ? "PUT" : "POST";
        const body = editId ? pacienteData : { ...pacienteData, id_paciente: crypto.randomUUID() };

        try {
            const respuesta = await fetchWithAuth(url, {
                method: method,
                headers: { "Content-Type": "application/json" },
                body: JSON.stringify(body),
            });
            if (!respuesta.ok) throw new Error((await respuesta.json()).detail || "Error del servidor");
            const resultado = await respuesta.json();
            alert(resultado.mensaje);
            setTimeout(() => {
                salirModoEdicion();
                cargarPacientes();
            }, 0);
        } catch (error) {
            if (error.message.includes("Token")) return;
            alert("Error al guardar paciente: " + error.message);
        }
    });
}

    function configurarFormularioCita() {
        const form = document.getElementById("formCita");
        if (!form) return;

        form.addEventListener("submit", async function(e) {
            e.preventDefault();
            const editId = form.getAttribute("data-edit-id");
            const idPacienteForm = document.getElementById("idPacienteCita").value.trim();
            const citaData = {
                id_paciente: idPacienteForm,
                fecha_hora: document.getElementById("fechaHoraCita").value,
                motivo: document.getElementById("motivoCita").value,
                estado: document.getElementById("estadoCita").value
            };

            if (editId) {
                
                const url = `/citas/${editId}`;
                try {
                    const respuesta = await fetchWithAuth(url, {
                        method: "PUT",
                        headers: { "Content-Type": "application/json" },
                        body: JSON.stringify(citaData),
                    });
                    if (!respuesta.ok) throw new Error((await respuesta.json()).detail || "Error del servidor");
                    const resultado = await respuesta.json();
                    alert(resultado.mensaje);
                    form.reset();
                    form.removeAttribute("data-edit-id");
                    document.getElementById("formCitaTitulo").textContent = "Registrar Cita";
                    form.querySelector("button[type='submit']").textContent = "Guardar Cita";
                    if (idPacienteActual && idPacienteActual === idPacienteForm) {
                        cargarHistorialPaciente(idPacienteActual);
                    }
                    configurarCalendario(); 
                } catch (error) {
                    if (error.message.includes("Token")) return;
                    alert("Error al actualizar la cita: " + error.message);
                }
            } else {
                const body = { ...citaData, id_cita: crypto.randomUUID() };
                await guardarNuevaCita(body, form, false); 
            }
        });
    }

    async function guardarNuevaCita(citaBody, form, force = false) {
        
        const url = force ? "/citas/?force=true" : "/citas/"; 
        try {
            const respuesta = await fetchWithAuth(url, {
                method: "POST",
                headers: { "Content-Type": "application/json" },
                body: JSON.stringify(citaBody),
            });
            if (!respuesta.ok) {
                if (respuesta.status === 409) { 
                    const error = await respuesta.json();
                    if (confirm(error.detail)) { 
                        await guardarNuevaCita(citaBody, form, true); 
                    }
                    return; 
                }
                throw new Error((await respuesta.json()).detail || "Error del servidor");
            }
            const resultado = await respuesta.json();
            alert(resultado.mensaje);
            form.reset();
            if (idPacienteActual && idPacienteActual === citaBody.id_paciente) {
                cargarHistorialPaciente(idPacienteActual);
            }
            configurarCalendario(); 
        } catch (error) {
            if (error.message.includes("Token")) return;
            alert("Error al guardar la cita: " + error.message);
        }
    }

    function configurarFormularioTratamiento() {
    const form = document.getElementById("formTratamiento");
    if (!form) return;
    form.addEventListener("submit", async function(e) {
        e.preventDefault();
        const editId = form.getAttribute("data-edit-id");
        
        // ✅ CORRECCIÓN: Convertir a string
        const duracionValor = document.getElementById("duracionValor").value;
        const duracionUnidad = document.getElementById("duracionUnidad").value;
        const duracionEstimada = `${duracionValor} ${duracionUnidad}`;
        
        const tratamiento = {
            nombre: document.getElementById("nombreTratamiento").value,
            categoria: document.getElementById("categoriaTratamiento").value,
            descripcion: document.getElementById("descripcionTratamiento").value,
            precio: document.getElementById("precioTratamiento").value,
            duracion_estimada: duracionEstimada  // ✅ Ahora es string
        };
        
        const url = editId ? `/tratamientos/${editId}` : "/tratamientos/";
        const method = editId ? "PUT" : "POST";
        const body = editId ? tratamiento : { ...tratamiento, id_tratamiento: crypto.randomUUID() };
        try {
            const respuesta = await fetchWithAuth(url, {
                method: method,
                headers: { "Content-Type": "application/json" },
                body: JSON.stringify(body),
            });
            if (!respuesta.ok) throw new Error((await respuesta.json()).detail || "Error del servidor");
            const resultado = await respuesta.json();
            alert(resultado.mensaje);
            form.reset();
            form.removeAttribute("data-edit-id");
            document.getElementById("formTratamientoTitulo").textContent = "Registrar Tratamiento";
            form.querySelector("button[type='submit']").textContent = "Guardar Tratamiento";
            cargarTratamientos();
        } catch (error) {
            if (error.message.includes("Token")) return;
            alert("Error al guardar el tratamiento: " + error.message);
        }
    });
}

    function configurarFormularioCitaTratamiento() {
        const form = document.getElementById("formCitaTratamiento");
        if (!form) return;
        form.addEventListener("submit", async function(e) {
            e.preventDefault();
            if (!idPacienteActual) {
                alert("Error: Para asignar un tratamiento, primero debe estar viendo el historial de un paciente.");
                return;
            }
            const relacion = {
                id_paciente: idPacienteActual,
                id_cita: document.getElementById("idCitaAsignar").value,
                id_tratamiento: document.getElementById("idTratamientoAsignar").value,
                observaciones: document.getElementById("observaciones").value,
                resultado: document.getElementById("resultado").value
            };
            try {
                
                const respuesta = await fetchWithAuth("/citas/cita-tratamiento", {
                    method: "POST",
                    headers: { "Content-Type": "application/json" },
                    body: JSON.stringify(relacion),
                });
                if (!respuesta.ok) throw new Error((await respuesta.json()).detail || "Error del servidor");
                const resultado = await respuesta.json();
                alert(resultado.mensaje);
                form.reset();
                cargarHistorialPaciente(idPacienteActual);
            } catch (error) {
                if (error.message.includes("Token")) return;
                alert("Error al asignar el tratamiento: " + error.message);
            }
        });
    }

    function configurarFormularioPago() {
        const form = document.getElementById("formPago");
        if (!form) return;
        form.addEventListener("submit", async function(e) {
            e.preventDefault();
            const editId = form.getAttribute("data-edit-id");
            const idCitaForm = form.getAttribute("data-cita-id") || document.getElementById("idCitaPago").value;

            if (!idPacienteActual) { alert("Error: No se pudo identificar al paciente."); return; }
            if (!idCitaForm) { alert("Error: No se pudo identificar la cita."); return; }

            const pago = {
                id_paciente: idPacienteActual,
                id_cita: idCitaForm,
                id_pago: editId || crypto.randomUUID(),
                monto: document.getElementById("montoPago").value,
                fecha_pago: document.getElementById("fechaPago").value,
                metodo_pago: document.getElementById("metodoPago").value
            };
            const method = editId ? "PUT" : "POST";
            
            const url = "/pagos/pago";

            try {
                const respuesta = await fetchWithAuth(url, {
                    method: method,
                    headers: { "Content-Type": "application/json" },
                    body: JSON.stringify(pago),
                });
                if (!respuesta.ok) throw new Error((await respuesta.json()).detail || "Error del servidor");
                const resultado = await respuesta.json();
                alert(resultado.mensaje);
                form.reset();
                form.removeAttribute("data-edit-id");
                form.removeAttribute("data-cita-id");
                document.getElementById("formPagoTitulo").textContent = "Registrar Pago de Cita";
                document.getElementById("btnSubmitPago").textContent = "Registrar Pago";
                cargarHistorialPaciente(idPacienteActual);
            } catch (error) {
                if (error.message.includes("Token")) return;
                alert("Error al registrar el pago: " + error.message);
            }
        });
    }

    function configurarFormularioAbono() {
        const form = document.getElementById("formAbono");
        if (!form) return;
        form.addEventListener("submit", async function(e) {
            e.preventDefault();
            const editId = form.getAttribute("data-edit-id");
            const idPacienteForm = document.getElementById("idPacienteAbono").value;
            if (!idPacienteForm) { alert("Error: Debe proveer un ID de Paciente."); return; }
            const abono = {
                id_paciente: idPacienteForm,
                id_abono: editId || crypto.randomUUID(),
                id_tratamiento: document.getElementById("idTratamientoAbono").value || null,
                fecha_abono: document.getElementById("fechaAbono").value,
                monto_abonado: document.getElementById("montoAbonado").value,
                saldo_restante: document.getElementById("saldoRestante").value,
                estado: document.getElementById("estadoAbono").value
            };
            const method = editId ? "PUT" : "POST";
            
            const url = "/pagos/abono";

            try {
                const respuesta = await fetchWithAuth(url, {
                    method: method,
                    headers: { "Content-Type": "application/json" },
                    body: JSON.stringify(abono),
                });
                if (!respuesta.ok) throw new Error((await respuesta.json()).detail || "Error del servidor");
                const resultado = await respuesta.json();
                alert(resultado.mensaje);
                form.reset();
                form.removeAttribute("data-edit-id");
                document.getElementById("formAbonoTitulo").textContent = "Registrar Abono a Cuenta";
                document.getElementById("btnSubmitAbono").textContent = "Registrar Abono";
                if(idPacienteActual && idPacienteActual === idPacienteForm) {
                    cargarHistorialPaciente(idPacienteActual);
                }
            } catch (error) {
                if (error.message.includes("Token")) return;
                alert("Error al registrar el abono: " + error.message);
            }
        });
    }

    function iniciarEdicionPago(id_pago, id_cita) {
        if (!historialPacienteActual) return;
        const cita = historialPacienteActual.citas_detalladas.find(c => c.id_cita === id_cita);
        if (!cita) return;
        const pago = cita.pagos.find(p => p.id_pago === id_pago);
        if (!pago) { alert("No se encontró el pago para editar."); return; }
        const form = document.getElementById("formPago");
        form.querySelector("#idCitaPago").value = pago.id_cita;
        form.querySelector("#montoPago").value = pago.monto;
        form.querySelector("#fechaPago").value = pago.fecha_pago;
        form.querySelector("#metodoPago").value = pago.metodo_pago;
        form.setAttribute("data-edit-id", id_pago);
        form.setAttribute("data-cita-id", id_cita);
        document.getElementById("formPagoTitulo").textContent = "Actualizar Pago";
        document.getElementById("btnSubmitPago").textContent = "Actualizar Pago";
        form.scrollIntoView({ behavior: 'smooth' });
    }

    async function eliminarPago(id_pago, id_cita) {
        if (!confirm("¿Seguro que quieres eliminar este pago?")) return;
        const body = { id_paciente: idPacienteActual, id_cita: id_cita, id_pago: id_pago };
        try {
            
            const respuesta = await fetchWithAuth("/pagos/pago", {
                method: 'DELETE',
                headers: { "Content-Type": "application/json" },
                body: JSON.stringify(body)
            });
            if (!respuesta.ok) throw new Error((await respuesta.json()).detail || "Error del servidor");
            const resultado = await respuesta.json();
            alert(resultado.mensaje);
            cargarHistorialPaciente(idPacienteActual); 
        } catch (error) {
            if (error.message.includes("Token")) return;
            alert("Error al eliminar el pago: " + error.message);
        }
    }

   function iniciarEdicionAbono(id_abono) {
    console.log("🔵 iniciarEdicionAbono llamado con ID:", id_abono);
    
    if (!historialPacienteActual) {
        console.log("❌ historialPacienteActual es null/undefined");
        alert("Error: No hay historial cargado");
        return;
    }
    
    console.log("📋 historialPacienteActual:", historialPacienteActual);
    console.log("📋 Abonos disponibles:", historialPacienteActual.abonos);
    
    const abono = historialPacienteActual.abonos.find(a => a.id_abono === id_abono);
    
    if (!abono) {
        console.log("❌ No se encontró el abono con ID:", id_abono);
        alert("No se encontró el abono para editar.");
        return;
    }
    
    console.log("✅ Abono encontrado:", abono);
    
    const form = document.getElementById("formAbono");
    if (!form) {
        console.log("❌ No se encontró el formulario con id 'formAbono'");
        alert("Error: No se encontró el formulario de abono");
        return;
    }
    
    console.log("✅ Formulario encontrado");
    
    const idPacienteInput = form.querySelector("#idPacienteAbono");
    const idTratamientoInput = form.querySelector("#idTratamientoAbono");
    const fechaInput = form.querySelector("#fechaAbono");
    const montoInput = form.querySelector("#montoAbonado");
    const saldoInput = form.querySelector("#saldoRestante");
    const estadoSelect = form.querySelector("#estadoAbono");
    
    console.log("Campos del formulario:");
    console.log("  idPacienteAbono:", idPacienteInput);
    console.log("  fechaAbono:", fechaInput);
    console.log("  montoAbonado:", montoInput);
    console.log("  saldoRestante:", saldoInput);
    console.log("  estadoAbono:", estadoSelect);
    
    if (idPacienteInput) idPacienteInput.value = abono.id_paciente;
    if (idTratamientoInput) idTratamientoInput.value = abono.id_tratamiento || "";
    if (fechaInput) fechaInput.value = abono.fecha_abono;
    if (montoInput) montoInput.value = abono.monto_abonado;
    if (saldoInput) saldoInput.value = abono.saldo_restante;
    if (estadoSelect) estadoSelect.value = abono.estado;
    
    form.setAttribute("data-edit-id", id_abono);
    
    const titulo = document.getElementById("formAbonoTitulo");
    if (titulo) titulo.textContent = "Actualizar Abono";
    
    const btnSubmit = document.getElementById("btnSubmitAbono");
    if (btnSubmit) btnSubmit.textContent = "Actualizar Abono";
    
    form.scrollIntoView({ behavior: 'smooth' });
    console.log("✅ Formulario llenado y desplazado");
}

    async function eliminarAbono(id_abono) {
        if (!confirm("¿Seguro que quieres eliminar este abono?")) return;
        const body = { id_paciente: idPacienteActual, id_abono: id_abono };
        try {
        
            const respuesta = await fetchWithAuth("/pagos/abono", {
                method: 'DELETE',
                headers: { "Content-Type": "application/json" },
                body: JSON.stringify(body)
            });
            if (!respuesta.ok) throw new Error((await respuesta.json()).detail || "Error del servidor");
            const resultado = await respuesta.json();
            alert(resultado.mensaje);
            cargarHistorialPaciente(idPacienteActual); 
        } catch (error) {
            if (error.message.includes("Token")) return;
            alert("Error al eliminar el abono: " + error.message);
        }
    }

    async function configurarCalendario() {
        const calendarioEl = document.getElementById("calendario");
        if (!calendarioEl) return;

        try {
            
            const respuesta = await fetchWithAuth("/citas/calendario");
            if (!respuesta.ok) throw new Error("No se pudieron cargar las citas del calendario");
            const eventos = await respuesta.json();
            const calendar = new FullCalendar.Calendar(calendarioEl, {
                initialView: 'timeGridWeek', 
                locale: 'es', 
                headerToolbar: {
                    left: 'prev,next today',
                    center: 'title',
                    right: 'dayGridMonth,timeGridWeek,timeGridDay' 
                },
                events: eventos, 
                nowIndicator: true,
                eventClick: function(info) {
                    alert(
                        'Paciente: ' + info.event.title + '\n' +
                        'Inicia: ' + info.event.start.toLocaleString() + '\n' +
                        'Termina: ' + (info.event.end ? info.event.end.toLocaleString() : 'N/A')
                    );
                }
            });
            calendar.render();
        } catch (error) {
            if (error.message.includes("Token")) return;
            calendarioEl.innerHTML = "<p style='color:red;'>Error al cargar el calendario.</p>";
            console.error("Error en configurarCalendario:", error);
        }
    }

    async function cargarDashboard() {
        const dashPacientes = document.getElementById("dashPacientes");
        if (!dashPacientes) return; 

        try {
            
            const respuesta = await fetchWithAuth("/reportes/dashboard/resumen");
            if (!respuesta.ok) return;
            const datos = await respuesta.json();

            dashPacientes.textContent = datos.total_pacientes;
            document.getElementById("dashCitas").textContent = datos.citas_mes;
            document.getElementById("dashIngresos").textContent = "$" + datos.ingresos_mes.toFixed(2);

            const ctx = document.getElementById('graficaIngresos');
            if (ctx) {
                if (window.miGrafica) window.miGrafica.destroy();
                window.miGrafica = new Chart(ctx, {
                    type: 'bar', 
                    data: {
                        labels: ['Pacientes Totales', 'Citas del Mes'],
                        datasets: [{
                            label: 'Estadísticas Generales',
                            data: [datos.total_pacientes, datos.citas_mes],
                            backgroundColor: ['#36a2eb', '#ffcd56'],
                            borderWidth: 1
                        }]
                    },
                    options: {
                        responsive: true,
                        scales: { y: { beginAtZero: true } }
                    }
                });
            }
        } catch (error) {
            console.error("Error dashboard:", error);
        }
    }

    init();
});








