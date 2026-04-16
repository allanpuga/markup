/**
 * Lógica de cálculo do Markup Motorista 2025
 * Baseado na página de referência https://markup2025-j6fhfdxm.manus.space/
 */

export interface CalculatorInputs {
  // Configurações gerais
  km_dia: number;
  dias_semana: number;
  horas_dia: number;
  margem: number;
  faturamento_semana: number;

  // Veículo
  fipe: number;
  depreciacao: number;
  parcela: number;
  seguro: number;
  licenciamento: number;

  // Combustível & Manutenção
  consumo_km: number;
  troca_oleo: number;
  pneus: number;
  manutencao: number;
  lavagem: number;
  alimentacao: number;

  // Outros custos
  inss: number;
  celular: number;

  // Localização & Impostos
  sel_estado: string;
  sel_cidade: string;
  iss: number;
  icms: number;
  ipva: number;
  preco_gas: number;
  ipca: number;
}

export interface CalculatorResults {
  // Markup por KM
  markup_km_urbano: number;
  markup_minuto_urbano: number;
  markup_km_intermunicipal: number;
  markup_minuto_intermunicipal: number;

  // Detalhamento de custos
  custos: {
    depreciacao: number;
    ipva: number;
    licenciamento: number;
    seguro: number;
    financiamento: number;
    inss: number;
    celular: number;
    alimentacao: number;
    combustivel: number;
    oleo: number;
    pneus: number;
    manutencao: number;
    lavagem: number;
    irpf: number;
    iss_valor: number;
    ipca_valor: number;
    icms_valor: number;
  };

  // Totais
  total_custos_iss: number;
  total_custos_icms: number;
  markup_final_iss: number;
  markup_final_icms: number;

  // Simulação Uber
  sim_calc_km: number;
  sim_calc_min: number;
  sim_total: number;

  // Custo por KM
  custo_km: number;

  // Valores por período
  por_km: {
    depreciacao: number;
    ipva: number;
    licenciamento: number;
    seguro: number;
    financiamento: number;
    inss: number;
    celular: number;
    alimentacao: number;
    combustivel: number;
    oleo: number;
    pneus: number;
    manutencao: number;
    lavagem: number;
    irpf: number;
    iss_valor: number;
    ipca_valor: number;
    icms_valor: number;
  };

  por_hora: {
    depreciacao: number;
    ipva: number;
    licenciamento: number;
    seguro: number;
    financiamento: number;
    inss: number;
    celular: number;
    alimentacao: number;
    combustivel: number;
    oleo: number;
    pneus: number;
    manutencao: number;
    lavagem: number;
    irpf: number;
    iss_valor: number;
    ipca_valor: number;
    icms_valor: number;
  };

  por_mes: {
    depreciacao: number;
    ipva: number;
    licenciamento: number;
    seguro: number;
    financiamento: number;
    inss: number;
    celular: number;
    alimentacao: number;
    combustivel: number;
    oleo: number;
    pneus: number;
    manutencao: number;
    lavagem: number;
    irpf: number;
    iss_valor: number;
    ipca_valor: number;
    icms_valor: number;
  };

  por_ano: {
    depreciacao: number;
    ipva: number;
    licenciamento: number;
    seguro: number;
    financiamento: number;
    inss: number;
    celular: number;
    alimentacao: number;
    combustivel: number;
    oleo: number;
    pneus: number;
    manutencao: number;
    lavagem: number;
    irpf: number;
    iss_valor: number;
    ipca_valor: number;
    icms_valor: number;
  };
}

export function calcularMarkup(inputs: CalculatorInputs): CalculatorResults {
  // Cálculos base
  const km_mes = inputs.km_dia * inputs.dias_semana * 4.33;
  const horas_mes = inputs.horas_dia * inputs.dias_semana * 4.33;
  const km_hora = km_mes > 0 ? km_mes / horas_mes : 0;

  // CUSTOS FIXOS
  const depreciacao_mes = (inputs.fipe * inputs.depreciacao) / 100 / 12;
  const ipva_mes = (inputs.fipe * inputs.ipva) / 100 / 12;
  const licenciamento_mes = inputs.licenciamento / 12;
  const seguro_mes = inputs.seguro / 12;
  const financiamento_mes = inputs.parcela;
  const inss_mes = inputs.inss;
  const celular_mes = inputs.celular;

  // CUSTOS VARIÁVEIS
  const combustivel_mes = (km_mes / inputs.consumo_km) * inputs.preco_gas;
  const oleo_mes = (inputs.troca_oleo / 10000) * km_mes;
  const pneus_mes = (inputs.pneus / 60000) * km_mes;
  const manutencao_mes = inputs.manutencao;
  const lavagem_mes = (inputs.lavagem / 7) * km_mes * 0.1;
  const alimentacao_mes = (inputs.alimentacao / 7) * km_mes * 0.1;

  // CUSTOS PERCENTUAIS
  const base_custos =
    depreciacao_mes +
    ipva_mes +
    licenciamento_mes +
    seguro_mes +
    financiamento_mes +
    inss_mes +
    celular_mes +
    combustivel_mes +
    oleo_mes +
    pneus_mes +
    manutencao_mes +
    lavagem_mes +
    alimentacao_mes;

  const iss_valor = (base_custos * inputs.iss) / 100;
  const icms_valor = (combustivel_mes * inputs.icms) / 100;
  const ipca_valor = (base_custos * inputs.ipca) / 100;
  const irpf_valor = 0; // Simplificado

  // TOTAIS
  const total_custos_iss =
    base_custos + iss_valor + ipca_valor - icms_valor;
  const total_custos_icms =
    base_custos + icms_valor + ipca_valor - iss_valor;

  // MARKUP COM MARGEM
  const margem_decimal = inputs.margem / 100;
  const markup_final_iss = total_custos_iss * (1 + margem_decimal);
  const markup_final_icms = total_custos_icms * (1 + margem_decimal);

  // CUSTO POR KM
  const custo_km = km_mes > 0 ? total_custos_iss / km_mes : 0;

  // MARKUP POR KM E MINUTO
  const markup_km_urbano = km_mes > 0 ? markup_final_iss / km_mes : 0;
  const markup_minuto_urbano =
    horas_mes > 0 ? markup_final_iss / (horas_mes * 60) : 0;
  const markup_km_intermunicipal = km_mes > 0 ? markup_final_icms / km_mes : 0;
  const markup_minuto_intermunicipal =
    horas_mes > 0 ? markup_final_icms / (horas_mes * 60) : 0;

  // SIMULAÇÃO UBER
  const uber_km = 20.6;
  const uber_valor = 23.43;
  const uber_tempo_min = 28;

  const sim_calc_km = markup_km_urbano * uber_km;
  const sim_calc_min = markup_minuto_urbano * uber_tempo_min;
  const sim_total = sim_calc_km + sim_calc_min;

  // Construir objeto de custos
  const custos = {
    depreciacao: depreciacao_mes,
    ipva: ipva_mes,
    licenciamento: licenciamento_mes,
    seguro: seguro_mes,
    financiamento: financiamento_mes,
    inss: inss_mes,
    celular: celular_mes,
    alimentacao: alimentacao_mes,
    combustivel: combustivel_mes,
    oleo: oleo_mes,
    pneus: pneus_mes,
    manutencao: manutencao_mes,
    lavagem: lavagem_mes,
    irpf: irpf_valor,
    iss_valor: iss_valor,
    ipca_valor: ipca_valor,
    icms_valor: icms_valor,
  };

  // Construir valores por período
  const por_km = Object.entries(custos).reduce(
    (acc, [key, value]) => {
      acc[key as keyof typeof custos] = km_mes > 0 ? value / km_mes : 0;
      return acc;
    },
    {} as typeof custos
  );

  const por_hora = Object.entries(custos).reduce(
    (acc, [key, value]) => {
      acc[key as keyof typeof custos] = horas_mes > 0 ? value / horas_mes : 0;
      return acc;
    },
    {} as typeof custos
  );

  const por_mes = custos;

  const por_ano = Object.entries(custos).reduce(
    (acc, [key, value]) => {
      acc[key as keyof typeof custos] = value * 12;
      return acc;
    },
    {} as typeof custos
  );

  return {
    markup_km_urbano,
    markup_minuto_urbano,
    markup_km_intermunicipal,
    markup_minuto_intermunicipal,
    custos,
    total_custos_iss,
    total_custos_icms,
    markup_final_iss,
    markup_final_icms,
    sim_calc_km,
    sim_calc_min,
    sim_total,
    custo_km,
    por_km,
    por_hora,
    por_mes,
    por_ano,
  };
}

export function formatCurrency(value: number): string {
  return new Intl.NumberFormat("pt-BR", {
    style: "currency",
    currency: "BRL",
  }).format(value);
}

export function formatNumber(value: number, decimals: number = 2): string {
  return value.toLocaleString("pt-BR", {
    minimumFractionDigits: decimals,
    maximumFractionDigits: decimals,
  });
}
