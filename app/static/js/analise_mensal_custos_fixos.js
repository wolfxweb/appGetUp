/**
 * CRUD de custos fixos — compartilhado entre wizard e cadastro rápido.
 */
let modalCustoFixo = null;
let modalGerenciarCustosFixos = null;

function formatCurrency(valor) {
    return new Intl.NumberFormat('pt-BR', {
        style: 'currency',
        currency: 'BRL'
    }).format(valor || 0);
}

function tratarErroAuth(response) {
    if (response.status === 401) {
        alert('Sua sessão expirou. Faça login novamente.');
        window.location.href = '/login';
        return true;
    }
    return false;
}

function initCustosFixosModais() {
    const elCusto = document.getElementById('modalCustoFixo');
    const elGerenciar = document.getElementById('modalGerenciarCustosFixos');
    if (elCusto) modalCustoFixo = new bootstrap.Modal(elCusto);
    if (elGerenciar) modalGerenciarCustosFixos = new bootstrap.Modal(elGerenciar);
}

function atualizarTotalCustosFixos(total) {
    const campoTotal = document.getElementById('custo_fixo_total');
    const modalTotal = document.getElementById('modal-custos-total');
    const valor = Number(total) || 0;
    if (campoTotal) campoTotal.value = valor > 0 ? valor.toFixed(2) : '';
    if (modalTotal) modalTotal.textContent = formatCurrency(valor);
    if (typeof formData !== 'undefined') {
        formData.custo_fixo_total = valor;
    }
    if (typeof atualizarCalculosParciais === 'function') {
        atualizarCalculosParciais();
    }
    if (typeof window.onCustoFixoTotalAtualizado === 'function') {
        window.onCustoFixoTotalAtualizado(valor);
    }
}

function abrirModalGerenciarCustosFixos() {
    carregarCustosFixos().then(() => {
        if (modalGerenciarCustosFixos) modalGerenciarCustosFixos.show();
    });
}

async function carregarCustosFixos(custoFixoSalvoNaAnalise) {
    try {
        const response = await fetch('/analise-mensal/api/custos-fixos', {
            credentials: 'include'
        });
        if (tratarErroAuth(response)) return;
        const data = await response.json();

        const tbody = document.getElementById('custos-cadastrados');
        const semCustos = document.getElementById('sem-custos');
        const tabela = document.getElementById('tabela-custos');

        let total = 0;

        if (data.custos && data.custos.length > 0) {
            if (tbody) tbody.innerHTML = '';

            data.custos.forEach(custo => {
                total += custo.valor;
                const nomeEscaped = custo.nome.replace(/'/g, "\\'").replace(/"/g, '\\"');
                const catEscaped = (custo.categoria || '').replace(/'/g, "\\'").replace(/"/g, '\\"');
                if (tbody) {
                    tbody.innerHTML += `
                        <tr>
                            <td>${custo.nome}</td>
                            <td>${custo.categoria}</td>
                            <td>${formatCurrency(custo.valor)}</td>
                            <td>
                                <button type="button" class="btn btn-sm btn-secondary me-1" onclick="editarCustoFixo(${custo.id}, '${nomeEscaped}', ${custo.valor}, '${catEscaped}')">
                                    <i class="bi bi-pencil"></i>
                                </button>
                                <button type="button" class="btn btn-sm btn-danger" onclick="excluirCustoFixo(${custo.id})">
                                    <i class="bi bi-trash"></i>
                                </button>
                            </td>
                        </tr>
                    `;
                }
            });

            if (semCustos) semCustos.style.display = 'none';
            if (tabela) tabela.style.display = '';
        } else {
            if (tbody) tbody.innerHTML = '';
            if (semCustos) semCustos.style.display = 'block';
            if (tabela) tabela.style.display = 'none';
        }

        const salvo = parseFloat(custoFixoSalvoNaAnalise) || 0;
        if (salvo > 0 && total === 0) {
            atualizarTotalCustosFixos(salvo);
        } else {
            atualizarTotalCustosFixos(total);
        }
    } catch (error) {
        console.error('Erro ao carregar custos fixos:', error);
    }
}

function abrirModalCustoFixo() {
    document.getElementById('custo_fixo_id').value = '';
    document.getElementById('custo_nome').value = '';
    document.getElementById('custo_valor').value = '';
    document.getElementById('custo_categoria').value = '';
    document.getElementById('modalCustoFixoLabel').textContent = 'Cadastrar Custo Fixo';
    modalCustoFixo.show();
}

function editarCustoFixo(id, nome, valor, categoria) {
    document.getElementById('custo_fixo_id').value = id;
    document.getElementById('custo_nome').value = nome;
    document.getElementById('custo_valor').value = valor;
    document.getElementById('custo_categoria').value = categoria;
    document.getElementById('modalCustoFixoLabel').textContent = 'Editar Custo Fixo';
    modalCustoFixo.show();
}

async function salvarCustoFixo() {
    const id = document.getElementById('custo_fixo_id').value;
    const nome = document.getElementById('custo_nome').value;
    const valor = parseFloat(document.getElementById('custo_valor').value);
    const categoria = document.getElementById('custo_categoria').value;

    if (!nome || !valor || !categoria) {
        alert('Preencha todos os campos.');
        return;
    }

    const method = id ? 'PUT' : 'POST';
    const url = id ? `/analise-mensal/api/custos-fixos/${id}` : '/analise-mensal/api/custos-fixos';

    try {
        const response = await fetch(url, {
            method: method,
            headers: { 'Content-Type': 'application/json' },
            credentials: 'include',
            body: JSON.stringify({ nome, valor, categoria })
        });

        if (tratarErroAuth(response)) return;

        const data = await response.json();

        if (response.ok) {
            modalCustoFixo.hide();
            await carregarCustosFixos();
            const msg = id ? 'Custo fixo atualizado com sucesso!' : 'Custo fixo cadastrado com sucesso!';
            ['custo-success-msg', 'custo-success-msg-modal'].forEach(elId => {
                const el = document.getElementById(elId);
                if (el) {
                    el.textContent = msg;
                    el.style.display = 'inline';
                    setTimeout(() => { el.style.display = 'none'; }, 3000);
                }
            });
        } else {
            alert('Erro ao salvar: ' + (data.detail || 'Erro desconhecido'));
        }
    } catch (error) {
        console.error('Erro ao salvar custo fixo:', error);
        alert('Erro ao salvar custo fixo.');
    }
}

async function excluirCustoFixo(id) {
    if (!confirm('Tem certeza que deseja excluir este custo fixo?')) return;

    try {
        const response = await fetch(`/analise-mensal/api/custos-fixos/${id}`, {
            method: 'DELETE',
            credentials: 'include'
        });

        if (tratarErroAuth(response)) return;

        if (response.ok) {
            carregarCustosFixos();
        } else {
            alert('Erro ao excluir custo fixo.');
        }
    } catch (error) {
        console.error('Erro ao excluir custo fixo:', error);
        alert('Erro ao excluir custo fixo.');
    }
}
