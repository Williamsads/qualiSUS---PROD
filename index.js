function logar() {
    const usuario = document.getElementById("usuario").value;
    const senha = document.getElementById("senha").value;
    const erro = document.getElementById("erro");

    erro.textContent = ""; // limpar erro

    if (usuario === "" || senha === "") {
        erro.textContent = "Preencha todos os campos!";
        return;
    }

    // Exemplo: Validação simples
    if (usuario === "admin" && senha === "12345") {
        alert("Login realizado com sucesso!");
        window.location.href = "home.html"; // redireciona
    } else {
        erro.textContent = "Usuário ou senha inválidos!";
    }
}
