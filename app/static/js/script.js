// Script personalizado

// Função para formatar o campo de WhatsApp
document.addEventListener('DOMContentLoaded', function() {
    const whatsappInput = document.getElementById('whatsapp');
    
    if (whatsappInput) {
        whatsappInput.addEventListener('input', function(e) {
            let value = e.target.value.replace(/\D/g, '');
            
            if (value.length > 11) {
                value = value.substring(0, 11);
            }
            
            // Formatar como (XX) XXXXX-XXXX
            if (value.length > 2) {
                value = '(' + value.substring(0, 2) + ') ' + value.substring(2);
            }
            if (value.length > 10) {
                value = value.substring(0, 10) + '-' + value.substring(10);
            }
            
            e.target.value = value;
        });
    }
    
    // Auto-fechar alertas após 5 segundos
    const alerts = document.querySelectorAll('.alert:not(.alert-permanent)');
    
    alerts.forEach(function(alert) {
        setTimeout(function() {
            alert.classList.add('fade');
            
            setTimeout(function() {
                alert.remove();
            }, 500);
        }, 5000);
    });


    // Tornar a função disponível globalmente
    window.buscarEnderecoPorCEP = buscarEnderecoPorCEP;

    // Formatar CEP
    const cepInput = document.getElementById('cep');
    if (cepInput) {
        cepInput.addEventListener('input', function(e) {
            let value = e.target.value.replace(/\D/g, '');
            if (value.length <= 8) {
                if (value.length > 5) {
                    value = value.substring(0,5) + '-' + value.substring(5);
                }
                e.target.value = value;
            }
        });

        // Buscar CEP ao pressionar Enter no campo
        cepInput.addEventListener('keypress', function(e) {
            if (e.key === 'Enter') {
                e.preventDefault();
                buscarEnderecoPorCEP();
            }
        });
    }
}); 