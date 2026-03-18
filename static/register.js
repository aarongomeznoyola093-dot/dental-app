document.addEventListener("DOMContentLoaded", () => {
    const viewRequest = document.getElementById("viewRequest");
    const viewVerify = document.getElementById("viewVerify");
    const btnRequestCode = document.getElementById("btnRequestCode");
    const registerForm = document.getElementById("registerForm");
    const statusEl = document.getElementById("status");

    const emailInput = document.getElementById("registerEmail");

    
    btnRequestCode.addEventListener("click", async () => {
        const email = emailInput.value;
        if (!email) {
            statusEl.textContent = "Por favor, ingresa un correo."; return;
        }

        statusEl.textContent = "Enviando código...";

        try {
            const respuesta = await fetch("/admin/request-registration-code", {
                method: "POST",
                headers: { "Content-Type": "application/json" },
                body: JSON.stringify({ email: email }),
            });

            const data = await respuesta.json();

            if (!respuesta.ok) {
                throw new Error(data.detail || "Error del servidor");
            }

            statusEl.textContent = data.mensaje;
            statusEl.style.color = "green";
            viewRequest.style.display = "none";
            viewVerify.style.display = "block";

        } catch (error) {
            statusEl.textContent = "Error: " + error.message;
            statusEl.style.color = "red";
        }
    });


    registerForm.addEventListener("submit", async (e) => {
        e.preventDefault();
        if (viewVerify.style.display === 'none') return; 

        const email = emailInput.value;
        const password = document.getElementById("registerPassword").value;
        const code = document.getElementById("registerCode").value;

        statusEl.textContent = "Registrando...";

        try {
            const respuesta = await fetch("/admin/complete-registration", {
                method: "POST",
                headers: { "Content-Type": "application/json" },
                body: JSON.stringify({
                    email: email,
                    password: password,
                    verification_code: code
                }),
            });

            const data = await respuesta.json();

            if (!respuesta.ok) {
                throw new Error(data.detail || "Error del servidor");
            }

            statusEl.textContent = data.mensaje + " Redirigiendo...";
            statusEl.style.color = "green";

            setTimeout(() => {
                window.location.href = "/app/login.html";
            }, 2000);

        } catch (error) {
            statusEl.textContent = "Error: " + error.message;
            statusEl.style.color = "red";
        }
    });

    
    const passwordInput = document.getElementById("registerPassword");
    
    
    passwordInput.addEventListener("input", () => {
        const val = passwordInput.value;
        
        const reqs = {
            length: val.length >= 8,
            upper: /[A-Z]/.test(val),
            number: /\d/.test(val),
            symbol: /[!@#$%^&*(),.?":{}|<>]/.test(val)
        };

        updateReq("req-length", reqs.length);
        updateReq("req-upper", reqs.upper);
        updateReq("req-number", reqs.number);
        updateReq("req-symbol", reqs.symbol);
    });

    function updateReq(elementId, isValid) {
        const el = document.getElementById(elementId);
        if (isValid) {
            el.textContent = " " + el.textContent.substring(2); 
            el.style.color = "green";
        } else {
            el.textContent = " " + el.textContent.substring(2);
            el.style.color = "#666";
        }
    }

    });
    