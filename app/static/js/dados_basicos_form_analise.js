/**
 * Salvamento de Dados Básicos em analise_mensal (formulário compartilhado com basic_data).
 * Depende de: converterParaNumero, formatarMoeda (basic_data_form.html), calcularCamposAnalise.
 */
(function () {
    'use strict';

    function getMesAno() {
        const monthEl = document.getElementById('month');
        const yearEl = document.getElementById('year');
        const mes = parseInt(monthEl.value, 10);
        const ano = parseInt(yearEl.value, 10);
        return { mes, ano };
    }

    function parseCapacidade() {
        const el = document.getElementById('service_capacity');
        if (!el || !el.value.trim()) return 0;
        const n = parseFloat(String(el.value).replace(',', '.'));
        return isNaN(n) ? 0 : n;
    }

    function getCustoFixoTotal() {
        const proEl = document.getElementById('pro_labore');
        const otherEl = document.getElementById('other_fixed_costs');
        const pro = proEl ? converterParaNumero(proEl.value) : 0;
        const other = otherEl ? converterParaNumero(otherEl.value) : 0;
        return pro + other;
    }

    function getGastosVendas() {
        const display = document.getElementById('sales_expenses_display');
        const hidden = document.getElementById('sales_expenses');
        if (display) return converterParaNumero(display.value);
        if (hidden) return converterParaNumero(hidden.value);
        return 0;
    }

    function getCustoMercadorias() {
        const display = document.getElementById('input_product_expenses_display');
        const hidden = document.getElementById('input_product_expenses');
        if (display) return converterParaNumero(display.value);
        if (hidden) return converterParaNumero(hidden.value);
        return 0;
    }

    function validarFormularioAnalise() {
        const { mes, ano } = getMesAno();
        if (!mes || !ano) {
            alert('Selecione o mês e o ano.');
            return false;
        }
        const clientesEl = document.getElementById('clients_served');
        const clientes = clientesEl ? parseInt(clientesEl.value, 10) : 0;
        const salesRevenueEl = document.getElementById('sales_revenue');
        const faturamento = salesRevenueEl ? converterParaNumero(salesRevenueEl.value) : 0;
        const custoFixo = getCustoFixoTotal();

        if (clientesEl && clientesEl.hasAttribute('required') && (!clientes || clientes < 0)) {
            alert('Informe a quantidade de clientes atendidos.');
            return false;
        }
        if (!faturamento || faturamento <= 0) {
            const fromCadastro = document.querySelector('[data-from-cadastro="1"]');
            if (!fromCadastro) {
                alert('Informe o faturamento ou cadastre seus produtos no perfil da loja.');
            } else {
                alert('Faturamento não encontrado no cadastro. Cadastre produtos ou atualize seu perfil.');
            }
            return false;
        }
        if (custoFixo <= 0) {
            alert('Informe os custos fixos (pró-labore e/ou demais custos fixos) ou cadastre custos fixos no sistema.');
            return false;
        }
        return true;
    }

    function montarPayloadAnalise() {
        const { mes, ano } = getMesAno();
        const clientesEl = document.getElementById('clients_served');
        const quantClientes = clientesEl ? (parseInt(clientesEl.value, 10) || 0) : 0;

        const base = {
            mes,
            ano,
            quant_clientes: quantClientes,
            capacidade_atendimento: parseCapacidade(),
            faturamento: converterParaNumero(document.getElementById('sales_revenue').value),
            gastos_vendas: getGastosVendas(),
            custo_mercadorias: getCustoMercadorias(),
            custo_fixo_total: getCustoFixoTotal(),
            corresponde_caixa: null,
        };

        if (typeof calcularCamposAnalise === 'function') {
            return Object.assign(base, calcularCamposAnalise(base));
        }
        return base;
    }

    function getPartnerLicenseId() {
        const pathMatch = window.location.pathname.match(/\/parceiro\/licencas\/(\d+)/);
        if (pathMatch) {
            return parseInt(pathMatch[1], 10);
        }
        if (window.PARTNER_LICENSE_ID != null && window.PARTNER_LICENSE_ID !== 'null') {
            return parseInt(window.PARTNER_LICENSE_ID, 10);
        }
        const form = document.getElementById('basicDataForm');
        if (form && form.dataset.partnerLicenseId) {
            return parseInt(form.dataset.partnerLicenseId, 10);
        }
        return null;
    }

    function isPartnerFormContext() {
        return window.location.pathname.startsWith('/parceiro/licencas/');
    }

    async function verificarDuplicataAnalise() {
        if (window.EDIT_MODE_ANALISE) return;
        const aviso = document.getElementById('aviso-duplicata');
        if (!aviso) return;

        const { mes, ano } = getMesAno();
        if (!mes || !ano) {
            aviso.style.display = 'none';
            return;
        }
        try {
            let url = `/analise-mensal/api/existe?mes=${mes}&ano=${ano}`;
            const partnerLicenseId = getPartnerLicenseId();
            if (partnerLicenseId) {
                url = `/parceiro/licencas/${partnerLicenseId}/api/existe?mes=${mes}&ano=${ano}`;
            }
            const response = await fetch(url, {
                credentials: 'include',
            });
            if (!response.ok) return;
            const data = await response.json();
            if (data.existe) {
                const editHref = data.edit_url || `/analise-mensal/cadastro/${data.analise_id}`;
                aviso.innerHTML = `Já existe um registro para este mês/ano. <a href="${editHref}">Editar registro existente</a>.`;
                aviso.style.display = 'block';
            } else {
                aviso.style.display = 'none';
            }
        } catch (e) {
            console.error(e);
        }
    }

    async function salvarDadosBasicosAnalise() {
        if (typeof updateHiddenFields === 'function') {
            updateHiddenFields();
        }
        if (!validarFormularioAnalise()) return;

        const btn = document.getElementById('btnSalvarAnalise');
        if (!btn) return;

        btn.disabled = true;
        const textoOriginal = btn.innerHTML;
        btn.innerHTML = '<span class="spinner-border spinner-border-sm me-2"></span>Salvando...';

        try {
            const payload = montarPayloadAnalise();
            const partnerLicenseId = getPartnerLicenseId();

            if (isPartnerFormContext() && !partnerLicenseId) {
                alert('Não foi possível identificar a licença do cliente. Volte pelo dashboard e abra Dados Básicos novamente.');
                return;
            }

            let saveUrl = '/analise-mensal/api/salvar';
            let redirectUrl = '/analise-mensal/lista?saved=1';
            if (partnerLicenseId) {
                saveUrl = `/parceiro/licencas/${partnerLicenseId}/api/salvar`;
                redirectUrl = `/parceiro/licencas/${partnerLicenseId}/dados-basicos/lista?success_message=Dados+básicos+salvos+com+sucesso`;
            }
            const response = await fetch(saveUrl, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                credentials: 'include',
                body: JSON.stringify(payload),
            });

            if (response.status === 401) {
                window.location.href = '/login';
                return;
            }

            const data = await response.json();
            if (data.success) {
                window.location.href = redirectUrl;
            } else {
                alert(data.message || 'Erro ao salvar dados básicos.');
            }
        } catch (error) {
            console.error(error);
            alert('Erro ao salvar dados básicos.');
        } finally {
            btn.disabled = false;
            btn.innerHTML = textoOriginal;
        }
    }

    function initDadosBasicosAnalise() {
        const monthEl = document.getElementById('month');
        const yearEl = document.getElementById('year');
        if (monthEl && !window.EDIT_MODE_ANALISE) {
            monthEl.addEventListener('change', verificarDuplicataAnalise);
        }
        if (yearEl && !window.EDIT_MODE_ANALISE) {
            yearEl.addEventListener('change', verificarDuplicataAnalise);
        }

        const btn = document.getElementById('btnSalvarAnalise');
        if (btn) {
            btn.addEventListener('click', salvarDadosBasicosAnalise);
        }
    }

    window.initDadosBasicosAnalise = initDadosBasicosAnalise;
    window.salvarDadosBasicosAnalise = salvarDadosBasicosAnalise;
})();
