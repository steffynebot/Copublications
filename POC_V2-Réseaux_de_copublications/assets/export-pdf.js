// assets/export_pdf.js

(function () {
    if (window.dash_export_pdf_initialized) {
        return;
    }
    window.dash_export_pdf_initialized = true;

    function exportDashboardToPDF() {
        const root = document.getElementById("page-wrapper");
        if (!root) {
            alert("Impossible de trouver la zone #page-wrapper à exporter.");
            return;
        }

        if (typeof html2canvas === "undefined") {
            alert("html2canvas n'est pas chargé (vérifie external_scripts dans app.py).");
            return;
        }

        if (!window.jspdf || !window.jspdf.jsPDF) {
            alert("jsPDF n'est pas chargé (vérifie external_scripts dans app.py).");
            return;
        }

        const { jsPDF } = window.jspdf;

        const width = root.scrollWidth;
        const height = root.scrollHeight;

        document.body.style.cursor = "progress";

        html2canvas(root, {
            scale: 2,
            useCORS: true,
            windowWidth: width,
            windowHeight: height,
        })
            .then(function (canvas) {
                const imgData = canvas.toDataURL("image/jpeg", 0.95);
                const pdf = new jsPDF("l", "mm", "a4"); // paysage

                const pageWidth = pdf.internal.pageSize.getWidth();
                const pageHeight = pdf.internal.pageSize.getHeight();

                const imgWidth = pageWidth;
                const imgHeight = (canvas.height * imgWidth) / canvas.width;

                let position = 0;
                let heightLeft = imgHeight;

                pdf.addImage(imgData, "JPEG", 0, position, imgWidth, imgHeight);
                heightLeft -= pageHeight;

                while (heightLeft > 0) {
                    position = heightLeft - imgHeight;
                    pdf.addPage();
                    pdf.addImage(
                        imgData,
                        "JPEG",
                        0,
                        position,
                        imgWidth,
                        imgHeight
                    );
                    heightLeft -= pageHeight;
                }

                pdf.save("copublications_inria.pdf");
            })
            .catch(function (err) {
                console.error("Erreur export PDF :", err);
                alert(
                    "Erreur lors de la génération du PDF, voir la console pour plus de détails."
                );
            })
            .finally(function () {
                document.body.style.cursor = "default";
            });
    }

    // 🔹 Event delegation : on n'a plus besoin que le bouton existe au chargement.
    document.addEventListener("click", function (e) {
        const btn = e.target.closest("#export-pdf");
        if (!btn) return;

        e.preventDefault();
        exportDashboardToPDF();
    });
})();
