// Script personalizado

// Mapeamento de estados
const estadosMap = {
    'AC': 'Acre',
    'AL': 'Alagoas',
    'AP': 'Amapá',
    'AM': 'Amazonas',
    'BA': 'Bahia',
    'CE': 'Ceará',
    'DF': 'Distrito Federal',
    'ES': 'Espírito Santo',
    'GO': 'Goiás',
    'MA': 'Maranhão',
    'MT': 'Mato Grosso',
    'MS': 'Mato Grosso do Sul',
    'MG': 'Minas Gerais',
    'PA': 'Pará',
    'PB': 'Paraíba',
    'PR': 'Paraná',
    'PE': 'Pernambuco',
    'PI': 'Piauí',
    'RJ': 'Rio de Janeiro',
    'RN': 'Rio Grande do Norte',
    'RS': 'Rio Grande do Sul',
    'RO': 'Rondônia',
    'RR': 'Roraima',
    'SC': 'Santa Catarina',
    'SP': 'São Paulo',
    'SE': 'Sergipe',
    'TO': 'Tocantins'
};

// Função para buscar endereço por CEP
function buscarEnderecoPorCEP() {
    const cepInput = document.getElementById('cep');
    const stateSelect = document.getElementById('state');
    const cityInput = document.getElementById('city');
    
    if (!cepInput || !stateSelect || !cityInput) {
        console.error('Elementos não encontrados');
        return;
    }
    
    const cep = cepInput.value.replace(/\D/g, '');
    
    if (cep.length !== 8) {
        alert('Por favor, informe um CEP válido com 8 dígitos.');
        return;
    }
    
    // Mostrar loading
    cepInput.disabled = true;
    stateSelect.disabled = true;
    cityInput.disabled = true;
    
    fetch(`https://viacep.com.br/ws/${cep}/json/`)
        .then(response => response.json())
        .then(data => {
            if (data.erro) {
                alert('CEP não encontrado. Verifique o número informado.');
                return;
            }
            
            // Preencher os campos
            if (data.uf && estadosMap[data.uf]) {
                stateSelect.value = data.uf;
            }
            
            if (data.localidade) {
                cityInput.value = data.localidade;
            }
            
            // Mostrar mensagem de sucesso
            const successAlert = document.createElement('div');
            successAlert.className = 'alert alert-success alert-dismissible fade show';
            successAlert.innerHTML = `
                <strong>Endereço encontrado!</strong> Estado e cidade preenchidos automaticamente.
                <button type="button" class="btn-close" data-bs-dismiss="alert"></button>
            `;
            
            const form = document.querySelector('form');
            if (form) {
                form.insertBefore(successAlert, form.firstChild);
            }
        })
        .catch(error => {
            console.error('Erro ao buscar CEP:', error);
            alert('Erro ao buscar o CEP. Verifique sua conexão com a internet e tente novamente.');
        })
        .finally(() => {
            // Reabilitar campos
            cepInput.disabled = false;
            stateSelect.disabled = false;
            cityInput.disabled = false;
        });
}

// Tornar a função disponível globalmente
window.buscarEnderecoPorCEP = buscarEnderecoPorCEP;

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
                if (typeof window.buscarEnderecoPorCEP === 'function') {
                    window.buscarEnderecoPorCEP();
                } else {
                    console.error('Função buscarEnderecoPorCEP não está disponível');
                }
            }
        });
    }
}); 