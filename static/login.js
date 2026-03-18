document.addEventListener("DOMContentLoaded", () => {
    const loginForm = document.getElementById("loginForm");
    const errorMessage = document.getElementById("error-message");


    if (sessionStorage.getItem("access_token")) {
        window.location.href = "/app/index.html";
    }

    loginForm.addEventListener("submit", async (event) => {
        event.preventDefault();
        errorMessage.textContent = "";

        const username = document.getElementById("username").value;
        const password = document.getElementById("password").value;
        
        const formData = new URLSearchParams();
        formData.append("username", username);
        formData.append("password", password);

        try {
            
            const response = await fetch("/admin/token", {
                method: "POST",
                headers: {
                    "Content-Type": "application/x-www-form-urlencoded",
                },
                body: formData,
            });

            if (response.ok) {
                const data = await response.json();
                sessionStorage.setItem("access_token", data.access_token);
                window.location.href = "/app/index.html";

            } else {
                const errorData = await response.json();
                errorMessage.textContent = errorData.detail || "Usuario o contraseña incorrectos.";
            }
        } catch (error) {
            errorMessage.textContent = "Error de conexión con el servidor.";
            console.error("Error al intentar iniciar sesión:", error);
        }
    });
});