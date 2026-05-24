/**
 * Cálculos compartilhados da análise mensal (espelham calcularResultadosF7 no wizard).
 */
function calcularCamposAnalise(dados) {
    const fat = dados.faturamento || 0;
    const gv = dados.gastos_vendas || 0;
    const cm = dados.custo_mercadorias || 0;
    const cf = dados.custo_fixo_total || 0;
    const qc = dados.quant_clientes || 0;

    const ticket_medio = qc > 0 ? fat / qc : 0;
    const margem_bruta = fat - gv - cm;
    const margem_contribuicao_por_cliente = qc > 0 ? margem_bruta / qc : 0;

    const margemPorCliente = qc > 0 ? margem_bruta / qc : 0;
    const peClientes = (margem_bruta > 0 && margemPorCliente > 0)
        ? cf / margemPorCliente
        : null;
    const peFaturamento = (peClientes != null && ticket_medio > 0)
        ? peClientes * ticket_medio
        : null;

    const ponto_equilibrio = peFaturamento || 0;
    const margem_seguranca = (peFaturamento != null && peFaturamento > 0 && fat > 0)
        ? ((fat - peFaturamento) / fat) * 100
        : null;

    const custo_total = gv + cm + cf;
    const resultado = fat - custo_total;
    const percentual_margem = fat > 0 ? (resultado / fat) * 100 : 0;

    return {
        ticket_medio,
        margem_bruta,
        margem_contribuicao_por_cliente,
        ponto_equilibrio,
        margem_seguranca,
        custo_total,
        resultado,
        percentual_margem
    };
}
