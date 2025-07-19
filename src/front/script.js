const BASE_API = "http://localhost:8000";
const ENDPOINT_UPLOADS = "/upload-pdfs";

document
  .getElementById("uploadForm")
  .addEventListener("submit", async function (e) {
    e.preventDefault();

    const status = document.getElementById("status");

    const funcionariosFile = document.getElementById(
      "uploadFuncionariosRelacao"
    ).files[0];
    const cartaoPontosFile =
      document.getElementById("uploadCartaoPontos").files[0];
    const cestaFile = document.getElementById("uploadCesta").files[0];
    const vtFile = document.getElementById("uploadVT").files[0];
    const substitutosFile = document.getElementById(
      "uploadFuncionariosSubstitutos"
    ).files[0];

    if (
      !funcionariosFile ||
      !cartaoPontosFile ||
      !cestaFile ||
      !vtFile ||
      !substitutosFile
    ) {
      status.innerText =
        "Por favor, envie arquivos para todas as seções obrigatórias.";
      return;
    }

    const formData = new FormData();

    formData.append("funcionarios", funcionariosFile);
    formData.append("cartao_pontos", cartaoPontosFile);
    formData.append("cesta", cestaFile);
    formData.append("vt", vtFile);
    formData.append("funcionarios_substitutos", substitutosFile);

    status.innerText = "Enviando arquivos...";

    try {
      const response = await fetch(BASE_API + ENDPOINT_UPLOADS, {
        method: "POST",
        body: formData,
      });

      if (!response.ok) throw new Error("Erro ao enviar.");

      const data = await response.json();
      console.log(data);
      gerarRelatorioPDF(data);
      status.innerText = "Relatório gerado com sucesso.";
    } catch (err) {
      console.warn("Erro no envio real. Executando mock...");
      status.innerText = "Erro no envio. Gerando relatório simulado...";
      setTimeout(() => gerarRelatorioPDF(gerarMock()), 1000);
    }
  });

  const tableData = funcionarios.map((f) => [
    f.nome,
    f.situacao,
    f.substituto ? "Sim" : "Não",
    f.tem_recibo ? "Sim" : "Não",
    f.tem_assinatura ? "Sim" : "Não",
    f.observacao || "",
    f.FGTS ? "OK" : "Não",
    f.INSS ? "OK" : "Não",
    f.VT ? "OK" : "Não",
  ]);

function calcularConformidade(f) {
  const totalCampos = 5;
  let emConformidade = 0;
  if (f.tem_recibo) emConformidade += 1;
  if (f.tem_assinatura) emConformidade += 1;
  if (f.VT) emConformidade += 1;
  if (f.FGTS) emConformidade += 1;
  if (f.INSS) emConformidade += 1;
  return Math.round((emConformidade / totalCampos) * 100);
}

function gerarMock() {
  const nomes = [
    "Fernanda Souza",
    "Ana Paula",
    "Carlos Silva",
    "João Mendes",
    "Marcos Oliveira",
    "Tatiane Ramos",
    "Bruno Lima",
    "Luana Rocha",
    "Eduardo Costa",
    "Juliana Alves",
  ];

  const cargos = [
    "Supervisora",
    "Auxiliar Administrativo",
    "Porteiro",
    "Zelador",
    "Assistente",
    "Analista",
    "Faxineira",
    "Recepcionista",
  ];

  const statusCesta = ["", "Entregue com atraso", "Não entregue"];

  const funcionarios = [];

  for (let i = 0; i < 20; i++) {
    const nome = nomes[Math.floor(Math.random() * nomes.length)];
    const cargo = cargos[Math.floor(Math.random() * cargos.length)];
    const horas = Math.floor(Math.random() * 21) + 140;
    const cesta = statusCesta[Math.floor(Math.random() * statusCesta.length)];
    const vt = Math.random() < 0.9;
    const salario = Math.random() < 0.85;
    const substituto = Math.random() < 0.5;
    const fgts = Math.random() < 0.85;
    const inss = Math.random() < 0.85;
    const vtObservacoes = Math.random() < 0.3 ? "Observação exemplo" : "";

    funcionarios.push({
      nome,
      cargo,
      horas,
      cesta,
      vt,
      salario,
      substituto,
      fgts,
      inss,
      vtObservacoes,
    });
  }

  return funcionarios;
}

function gerarRelatorioPDF(data) {
  const { jsPDF } = window.jspdf;
  const doc = new jsPDF();

  const funcionarios = data.data;

  if (!Array.isArray(funcionarios) || funcionarios.length === 0) {
    alert("Nenhum dado para gerar o relatório.");
    return;
  }

  const headers = [
    ["Nome", "Situação", "Substituto", "Cesta Básica", "Assinatura CB", "Observação", "FGTS", "INSS", "VT"],
  ];

  funcionarios.sort(
    (a, b) => calcularConformidade(a) - calcularConformidade(b)
  );

 const tableData = funcionarios.map((f) => [
    f.nome,
    f.situacao,
    f.substituto ? "Sim" : "Não",
    f.tem_recibo ? "Sim" : "Não",
    f.tem_assinatura ? "Sim" : "Não",
    f.observacao || "",
    f.FGTS ? "OK" : "Não",
    f.INSS ? "OK" : "Não",
    f.VT ? "OK" : "Não",
  ]);

  const mediaConformidade =
    funcionarios.reduce((acc, f) => acc + calcularConformidade(f), 0) /
    funcionarios.length;

  doc.setFontSize(14);
  doc.text(
    "Relatório de Pendências Contratuais",
    105,
    15,
    null,
    null,
    "center"
  );

  doc.setFontSize(12);
  doc.text(
    `Conformidade geral (benefícios obrigatórios): ${mediaConformidade.toFixed(
      1
    )}%`,
    105,
    23,
    null,
    null,
    "center"
  );

  // Divisor horizontal
  doc.setDrawColor(0, 0, 0);
  doc.setLineWidth(0.5);
  doc.line(15, 27, 195, 27);

  // Gerar tabela e capturar final do conteúdo gerado (usar hook didDrawPage)
  let finalY = 0;
  doc.autoTable({
    head: headers,
    body: tableData,
    startY: 32,
    styles: { halign: "center" },
    headStyles: { fillColor: [0, 51, 102], textColor: 255 },
    didDrawPage: (data) => {
      finalY = data.cursor.y;
    },
  });

  // Preparar lista de observações de cesta pendente
  const observacoesCesta = funcionarios
    .filter((f) => f.cesta !== "")
    .map((f) => `${f.nome} está com Cesta Básica ${f.cesta}`);

  if (observacoesCesta.length > 0) {
    // Definir espaço entre linhas e margem inferior da página
    const lineHeight = 6;
    const pageHeight = doc.internal.pageSize.height;
    const bottomMargin = 15;

    let y = finalY + 10;

    // Se não couber no espaço restante, criar nova página
    if (y + observacoesCesta.length * lineHeight > pageHeight - bottomMargin) {
      doc.addPage();
      y = 20;
    }

    doc.setFontSize(12);
    doc.text("Observações", 105, y, null, null, "center");
    y += 5;

    doc.setDrawColor(0, 0, 0);
    doc.setLineWidth(0.3);
    doc.line(15, y, 195, y);
    y += 5;

    doc.setFontSize(10);
    doc.setTextColor(0);

    doc.text(data.analise, 15, y);
  }

  doc.save("relatorio.pdf");
}

// Botão limpar
document.getElementById("btnClear").addEventListener("click", () => {
  [
    "uploadFuncionariosRelacao",
    "uploadCartaoPontos",
    "uploadCesta",
    "uploadVT",
    "uploadFuncionariosSubstitutos",
  ].forEach((id) => {
    document.getElementById(id).value = "";
  });
  document.getElementById("status").innerText = "";
});

// Adicionar evento para limpar input individual ao clicar no ícone
document.querySelectorAll(".clear-icon").forEach((icon) => {
  icon.addEventListener("click", () => {
    const targetId = icon.getAttribute("data-target");
    const input = document.getElementById(targetId);
    if (input) {
      input.value = "";
      input.dispatchEvent(new Event("change"));
      icon.style.display = "none";
    }
  });
});

// Mostrar/ocultar ícone baseado no input preenchido
document.querySelectorAll("input[type=file]").forEach((input) => {
  input.addEventListener("change", () => {
    const icon = input.parentElement.querySelector(".clear-icon");
    if (icon) {
      icon.style.display = input.value ? "block" : "none";
    }
  });
});
