import { useEffect, useState } from "react";
import { CalculatorInputs, CalculatorResults, calcularMarkup, formatCurrency, formatNumber } from "@/lib/calculator";
import { estadosData } from "@/data/estados";

export default function Home() {
  const [inputs, setInputs] = useState<CalculatorInputs>({
    km_dia: 230,
    dias_semana: 6,
    horas_dia: 10,
    margem: 20,
    faturamento_semana: 2340,
    fipe: 62333,
    depreciacao: 24,
    parcela: 1660,
    seguro: 4200,
    licenciamento: 175,
    consumo_km: 10,
    troca_oleo: 350,
    pneus: 1800,
    manutencao: 350,
    lavagem: 70,
    alimentacao: 140,
    inss: 166.98,
    celular: 180,
    sel_estado: "",
    sel_cidade: "",
    iss: 5,
    icms: 12,
    ipva: 4,
    preco_gas: 6.2,
    ipca: 4.83,
  });

  const [results, setResults] = useState<CalculatorResults | null>(null);
  const [cidades, setCidades] = useState<string[]>([]);

  useEffect(() => {
    calcular();
  }, [inputs]);

  const calcular = () => {
    const res = calcularMarkup(inputs);
    setResults(res);
  };

  const handleInputChange = (field: keyof CalculatorInputs, value: any) => {
    setInputs((prev) => ({
      ...prev,
      [field]: value,
    }));
  };

  const handleEstadoChange = (uf: string) => {
    handleInputChange("sel_estado", uf);
    handleInputChange("sel_cidade", "");
    setCidades([]);

    if (uf && estadosData[uf]) {
      const estado = estadosData[uf];
      handleInputChange("icms", estado.icms);
      handleInputChange("ipva", estado.ipva);
      handleInputChange("preco_gas", estado.gas);
      setCidades(Object.keys(estado.cidades).sort());
    }
  };

  const handleCidadeChange = (cidade: string) => {
    handleInputChange("sel_cidade", cidade);

    if (inputs.sel_estado && cidade && estadosData[inputs.sel_estado]) {
      const estado = estadosData[inputs.sel_estado];
      const iss = estado.cidades[cidade];
      if (iss) {
        handleInputChange("iss", iss);
      }
    }
  };

  const resetar = () => {
    setInputs({
      km_dia: 230,
      dias_semana: 6,
      horas_dia: 10,
      margem: 20,
      faturamento_semana: 2340,
      fipe: 62333,
      depreciacao: 24,
      parcela: 1660,
      seguro: 4200,
      licenciamento: 175,
      consumo_km: 10,
      troca_oleo: 350,
      pneus: 1800,
      manutencao: 350,
      lavagem: 70,
      alimentacao: 140,
      inss: 166.98,
      celular: 180,
      sel_estado: "",
      sel_cidade: "",
      iss: 5,
      icms: 12,
      ipva: 4,
      preco_gas: 6.2,
      ipca: 4.83,
    });
    setCidades([]);
  };

  return (
    <div className="min-h-screen bg-gradient-to-br from-slate-900 via-slate-800 to-slate-900">
      {/* Header */}
      <header className="border-b border-amber-500/30 bg-gradient-to-r from-slate-900 to-slate-800 px-6 py-8">
        <div className="mx-auto max-w-6xl">
          <div className="mb-4 inline-block rounded bg-amber-500 px-3 py-1 text-xs font-bold uppercase tracking-wider text-black">
            Motorista App · Brasil
          </div>
          <h1 className="mb-2 text-4xl font-black text-white">
            MARKUP <span className="text-amber-500">MOTORISTA</span>
          </h1>
          <p className="text-sm text-slate-400">
            Calculadora de precificação para Uber, 99, inDriver e similares
          </p>
          <div className="mt-4 inline-block rounded-full border border-green-500/40 bg-green-500/10 px-4 py-2 text-xs font-semibold text-green-400">
            ✓ Valores atualizados 2025
          </div>
        </div>
      </header>

      {/* Main Content */}
      <div className="mx-auto max-w-6xl px-6 py-12">
        <div className="grid gap-8 lg:grid-cols-2">
          {/* Coluna 1: Inputs */}
          <div className="space-y-6">
            {/* Configurações Gerais */}
            <div className="rounded-lg border border-slate-700 bg-slate-800/50 p-6 backdrop-blur">
              <div className="mb-6 flex items-center gap-2 text-sm font-bold uppercase tracking-wider text-amber-500">
                <svg className="h-4 w-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <circle cx="12" cy="12" r="10"></circle>
                  <path d="M12 6v6l4 2"></path>
                </svg>
                Configurações Gerais
              </div>
              <div className="grid gap-4 sm:grid-cols-3">
                <div>
                  <label className="mb-2 block text-xs font-semibold uppercase text-slate-400">KM por dia</label>
                  <input
                    type="number"
                    value={inputs.km_dia}
                    onChange={(e) => handleInputChange("km_dia", parseFloat(e.target.value))}
                    className="w-full rounded border border-slate-600 bg-slate-700 px-3 py-2 text-white focus:border-amber-500 focus:outline-none"
                  />
                </div>
                <div>
                  <label className="mb-2 block text-xs font-semibold uppercase text-slate-400">Dias/semana</label>
                  <input
                    type="number"
                    value={inputs.dias_semana}
                    onChange={(e) => handleInputChange("dias_semana", parseFloat(e.target.value))}
                    className="w-full rounded border border-slate-600 bg-slate-700 px-3 py-2 text-white focus:border-amber-500 focus:outline-none"
                  />
                </div>
                <div>
                  <label className="mb-2 block text-xs font-semibold uppercase text-slate-400">Horas/dia</label>
                  <input
                    type="number"
                    value={inputs.horas_dia}
                    onChange={(e) => handleInputChange("horas_dia", parseFloat(e.target.value))}
                    className="w-full rounded border border-slate-600 bg-slate-700 px-3 py-2 text-white focus:border-amber-500 focus:outline-none"
                  />
                </div>
              </div>
              <div className="mt-4 grid gap-4 sm:grid-cols-2">
                <div>
                  <label className="mb-2 block text-xs font-semibold uppercase text-slate-400">Margem de lucro desejada (%)</label>
                  <input
                    type="number"
                    value={inputs.margem}
                    onChange={(e) => handleInputChange("margem", parseFloat(e.target.value))}
                    className="w-full rounded border border-slate-600 bg-slate-700 px-3 py-2 text-white focus:border-amber-500 focus:outline-none"
                  />
                </div>
                <div>
                  <label className="mb-2 block text-xs font-semibold uppercase text-slate-400">Faturamento bruto / semana (R$)</label>
                  <input
                    type="number"
                    value={inputs.faturamento_semana}
                    onChange={(e) => handleInputChange("faturamento_semana", parseFloat(e.target.value))}
                    className="w-full rounded border border-slate-600 bg-slate-700 px-3 py-2 text-white focus:border-amber-500 focus:outline-none"
                  />
                </div>
              </div>
            </div>

            {/* Veículo */}
            <div className="rounded-lg border border-slate-700 bg-slate-800/50 p-6 backdrop-blur">
              <div className="mb-6 flex items-center gap-2 text-sm font-bold uppercase tracking-wider text-amber-500">
                <svg className="h-4 w-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path d="M12 2C6.48 2 2 6.48 2 12s4.48 10 10 10 10-4.48 10-10S17.52 2 12 2z"></path>
                </svg>
                Veículo
              </div>
              <div className="grid gap-4 sm:grid-cols-2">
                <div>
                  <label className="mb-2 block text-xs font-semibold uppercase text-slate-400">Valor FIPE do veículo (R$)</label>
                  <input
                    type="number"
                    value={inputs.fipe}
                    onChange={(e) => handleInputChange("fipe", parseFloat(e.target.value))}
                    className="w-full rounded border border-slate-600 bg-slate-700 px-3 py-2 text-white focus:border-amber-500 focus:outline-none"
                  />
                </div>
                <div>
                  <label className="mb-2 block text-xs font-semibold uppercase text-slate-400">Depreciação anual (%)</label>
                  <input
                    type="number"
                    value={inputs.depreciacao}
                    onChange={(e) => handleInputChange("depreciacao", parseFloat(e.target.value))}
                    className="w-full rounded border border-slate-600 bg-slate-700 px-3 py-2 text-white focus:border-amber-500 focus:outline-none"
                  />
                </div>
              </div>
              <div className="mt-4 grid gap-4 sm:grid-cols-2">
                <div>
                  <label className="mb-2 block text-xs font-semibold uppercase text-slate-400">Parcela / Aluguel mensal (R$)</label>
                  <input
                    type="number"
                    value={inputs.parcela}
                    onChange={(e) => handleInputChange("parcela", parseFloat(e.target.value))}
                    className="w-full rounded border border-slate-600 bg-slate-700 px-3 py-2 text-white focus:border-amber-500 focus:outline-none"
                  />
                </div>
                <div>
                  <label className="mb-2 block text-xs font-semibold uppercase text-slate-400">Seguro anual (R$)</label>
                  <input
                    type="number"
                    value={inputs.seguro}
                    onChange={(e) => handleInputChange("seguro", parseFloat(e.target.value))}
                    className="w-full rounded border border-slate-600 bg-slate-700 px-3 py-2 text-white focus:border-amber-500 focus:outline-none"
                  />
                </div>
              </div>
              <div className="mt-4">
                <label className="mb-2 block text-xs font-semibold uppercase text-slate-400">Licenciamento + DPVAT (R$)</label>
                <input
                  type="number"
                  value={inputs.licenciamento}
                  onChange={(e) => handleInputChange("licenciamento", parseFloat(e.target.value))}
                  className="w-full rounded border border-slate-600 bg-slate-700 px-3 py-2 text-white focus:border-amber-500 focus:outline-none"
                />
              </div>
            </div>

            {/* Combustível & Manutenção */}
            <div className="rounded-lg border border-slate-700 bg-slate-800/50 p-6 backdrop-blur">
              <div className="mb-6 flex items-center gap-2 text-sm font-bold uppercase tracking-wider text-amber-500">
                <svg className="h-4 w-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path d="M12 2L2 7l10 5 10-5-10-5zM2 17l10 5 10-5M2 12l10 5 10-5"></path>
                </svg>
                Combustível & Manutenção
              </div>
              <div className="grid gap-4 sm:grid-cols-2">
                <div>
                  <label className="mb-2 block text-xs font-semibold uppercase text-slate-400">Consumo (km/litro)</label>
                  <input
                    type="number"
                    value={inputs.consumo_km}
                    onChange={(e) => handleInputChange("consumo_km", parseFloat(e.target.value))}
                    className="w-full rounded border border-slate-600 bg-slate-700 px-3 py-2 text-white focus:border-amber-500 focus:outline-none"
                  />
                </div>
                <div>
                  <label className="mb-2 block text-xs font-semibold uppercase text-slate-400">Troca de óleo (custo) (R$)</label>
                  <input
                    type="number"
                    value={inputs.troca_oleo}
                    onChange={(e) => handleInputChange("troca_oleo", parseFloat(e.target.value))}
                    className="w-full rounded border border-slate-600 bg-slate-700 px-3 py-2 text-white focus:border-amber-500 focus:outline-none"
                  />
                </div>
              </div>
              <div className="mt-4 grid gap-4 sm:grid-cols-2">
                <div>
                  <label className="mb-2 block text-xs font-semibold uppercase text-slate-400">4 pneus (60 mil km) (R$)</label>
                  <input
                    type="number"
                    value={inputs.pneus}
                    onChange={(e) => handleInputChange("pneus", parseFloat(e.target.value))}
                    className="w-full rounded border border-slate-600 bg-slate-700 px-3 py-2 text-white focus:border-amber-500 focus:outline-none"
                  />
                </div>
                <div>
                  <label className="mb-2 block text-xs font-semibold uppercase text-slate-400">Manutenção prev./mês (R$)</label>
                  <input
                    type="number"
                    value={inputs.manutencao}
                    onChange={(e) => handleInputChange("manutencao", parseFloat(e.target.value))}
                    className="w-full rounded border border-slate-600 bg-slate-700 px-3 py-2 text-white focus:border-amber-500 focus:outline-none"
                  />
                </div>
              </div>
              <div className="mt-4 grid gap-4 sm:grid-cols-2">
                <div>
                  <label className="mb-2 block text-xs font-semibold uppercase text-slate-400">Lavagem / semana (R$)</label>
                  <input
                    type="number"
                    value={inputs.lavagem}
                    onChange={(e) => handleInputChange("lavagem", parseFloat(e.target.value))}
                    className="w-full rounded border border-slate-600 bg-slate-700 px-3 py-2 text-white focus:border-amber-500 focus:outline-none"
                  />
                </div>
                <div>
                  <label className="mb-2 block text-xs font-semibold uppercase text-slate-400">Alimentação / semana (R$)</label>
                  <input
                    type="number"
                    value={inputs.alimentacao}
                    onChange={(e) => handleInputChange("alimentacao", parseFloat(e.target.value))}
                    className="w-full rounded border border-slate-600 bg-slate-700 px-3 py-2 text-white focus:border-amber-500 focus:outline-none"
                  />
                </div>
              </div>
            </div>

            {/* Outros Custos */}
            <div className="rounded-lg border border-slate-700 bg-slate-800/50 p-6 backdrop-blur">
              <div className="mb-6 flex items-center gap-2 text-sm font-bold uppercase tracking-wider text-amber-500">
                <svg className="h-4 w-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path d="M12 2C6.48 2 2 6.48 2 12s4.48 10 10 10 10-4.48 10-10S17.52 2 12 2z"></path>
                </svg>
                Outros Custos Fixos
              </div>
              <div className="grid gap-4 sm:grid-cols-2">
                <div>
                  <label className="mb-2 block text-xs font-semibold uppercase text-slate-400">INSS mensal (R$)</label>
                  <input
                    type="number"
                    value={inputs.inss}
                    onChange={(e) => handleInputChange("inss", parseFloat(e.target.value))}
                    className="w-full rounded border border-slate-600 bg-slate-700 px-3 py-2 text-white focus:border-amber-500 focus:outline-none"
                  />
                </div>
                <div>
                  <label className="mb-2 block text-xs font-semibold uppercase text-slate-400">Celular / Internet mensal (R$)</label>
                  <input
                    type="number"
                    value={inputs.celular}
                    onChange={(e) => handleInputChange("celular", parseFloat(e.target.value))}
                    className="w-full rounded border border-slate-600 bg-slate-700 px-3 py-2 text-white focus:border-amber-500 focus:outline-none"
                  />
                </div>
              </div>
            </div>

            {/* Localização */}
            <div className="rounded-lg border border-slate-700 bg-slate-800/50 p-6 backdrop-blur">
              <div className="mb-6 flex items-center gap-2 text-sm font-bold uppercase tracking-wider text-amber-500">
                <svg className="h-4 w-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path d="M21 10c0 7-9 13-9 13s-9-6-9-13a9 9 0 0 1 18 0z"></path>
                  <circle cx="12" cy="10" r="3"></circle>
                </svg>
                Localização — Impostos Automáticos
              </div>
              <div className="grid gap-4">
                <div>
                  <label className="mb-2 block text-xs font-semibold uppercase text-slate-400">Estado</label>
                  <select
                    value={inputs.sel_estado}
                    onChange={(e) => handleEstadoChange(e.target.value)}
                    className="w-full rounded border border-slate-600 bg-slate-700 px-3 py-2 text-white focus:border-amber-500 focus:outline-none"
                  >
                    <option value="">— Selecione o estado —</option>
                    {Object.entries(estadosData)
                      .sort((a, b) => a[1].nome.localeCompare(b[1].nome))
                      .map(([uf, data]) => (
                        <option key={uf} value={uf}>
                          {data.nome} ({uf})
                        </option>
                      ))}
                  </select>
                </div>
                <div>
                  <label className="mb-2 block text-xs font-semibold uppercase text-slate-400">Cidade</label>
                  <select
                    value={inputs.sel_cidade}
                    onChange={(e) => handleCidadeChange(e.target.value)}
                    disabled={!inputs.sel_estado}
                    className="w-full rounded border border-slate-600 bg-slate-700 px-3 py-2 text-white disabled:opacity-50 focus:border-amber-500 focus:outline-none"
                  >
                    <option value="">— Selecione a cidade —</option>
                    {cidades.map((cidade) => (
                      <option key={cidade} value={cidade}>
                        {cidade}
                      </option>
                    ))}
                  </select>
                </div>
              </div>
            </div>

            {/* Impostos Editáveis */}
            <div className="rounded-lg border border-slate-700 bg-slate-800/50 p-6 backdrop-blur">
              <div className="mb-6 text-sm font-bold uppercase tracking-wider text-amber-500">Valores carregados (editáveis manualmente)</div>
              <div className="grid gap-4 sm:grid-cols-2">
                <div>
                  <label className="mb-2 block text-xs font-semibold uppercase text-slate-400">ISS (cidade) (%)</label>
                  <input
                    type="number"
                    value={inputs.iss}
                    onChange={(e) => handleInputChange("iss", parseFloat(e.target.value))}
                    className="w-full rounded border border-slate-600 bg-slate-700 px-3 py-2 text-white focus:border-amber-500 focus:outline-none"
                  />
                </div>
                <div>
                  <label className="mb-2 block text-xs font-semibold uppercase text-slate-400">ICMS (intermun.) (%)</label>
                  <input
                    type="number"
                    value={inputs.icms}
                    onChange={(e) => handleInputChange("icms", parseFloat(e.target.value))}
                    className="w-full rounded border border-slate-600 bg-slate-700 px-3 py-2 text-white focus:border-amber-500 focus:outline-none"
                  />
                </div>
              </div>
              <div className="mt-4 grid gap-4 sm:grid-cols-2">
                <div>
                  <label className="mb-2 block text-xs font-semibold uppercase text-slate-400">IPVA (estado) (%)</label>
                  <input
                    type="number"
                    value={inputs.ipva}
                    onChange={(e) => handleInputChange("ipva", parseFloat(e.target.value))}
                    className="w-full rounded border border-slate-600 bg-slate-700 px-3 py-2 text-white focus:border-amber-500 focus:outline-none"
                  />
                </div>
                <div>
                  <label className="mb-2 block text-xs font-semibold uppercase text-slate-400">Gasolina / litro na região (R$)</label>
                  <input
                    type="number"
                    value={inputs.preco_gas}
                    onChange={(e) => handleInputChange("preco_gas", parseFloat(e.target.value))}
                    className="w-full rounded border border-slate-600 bg-slate-700 px-3 py-2 text-white focus:border-amber-500 focus:outline-none"
                  />
                </div>
              </div>
              <div className="mt-4">
                <label className="mb-2 block text-xs font-semibold uppercase text-slate-400">IPCA inflação 2024 (%)</label>
                <input
                  type="number"
                  value={inputs.ipca}
                  onChange={(e) => handleInputChange("ipca", parseFloat(e.target.value))}
                  className="w-full rounded border border-slate-600 bg-slate-700 px-3 py-2 text-white focus:border-amber-500 focus:outline-none"
                />
              </div>
            </div>

            {/* Botões */}
            <div className="flex gap-4">
              <button
                onClick={calcular}
                className="flex-1 rounded-lg bg-amber-500 px-6 py-3 font-bold text-black hover:bg-amber-600 transition"
              >
                ⚡ CALCULAR MEU MARKUP
              </button>
              <button
                onClick={resetar}
                className="flex-1 rounded-lg border border-slate-600 px-6 py-3 font-bold text-white hover:bg-slate-700 transition"
              >
                Resetar
              </button>
            </div>
          </div>

          {/* Coluna 2: Resultados */}
          {results && (
            <div className="space-y-6">
              {/* Cards de Resultado */}
              <div className="grid gap-4 sm:grid-cols-2">
                <div className="rounded-lg border border-amber-500/50 bg-gradient-to-br from-amber-500/10 to-amber-500/5 p-4">
                  <div className="text-xs font-bold uppercase tracking-wider text-slate-400">Markup / KM</div>
                  <div className="mt-2 text-3xl font-bold text-white">
                    R${formatNumber(results.markup_km_urbano, 2)}
                  </div>
                  <div className="mt-1 text-xs text-slate-400">Corridas urbanas</div>
                  <div className="mt-2 inline-block rounded-full bg-amber-500/20 px-2 py-1 text-xs font-bold text-amber-400">
                    ISS
                  </div>
                </div>

                <div className="rounded-lg border border-amber-500/50 bg-gradient-to-br from-amber-500/10 to-amber-500/5 p-4">
                  <div className="text-xs font-bold uppercase tracking-wider text-slate-400">Markup / Minuto</div>
                  <div className="mt-2 text-3xl font-bold text-white">
                    R${formatNumber(results.markup_minuto_urbano, 2)}
                  </div>
                  <div className="mt-1 text-xs text-slate-400">Corridas urbanas</div>
                  <div className="mt-2 inline-block rounded-full bg-amber-500/20 px-2 py-1 text-xs font-bold text-amber-400">
                    ISS
                  </div>
                </div>

                <div className="rounded-lg border border-blue-500/50 bg-gradient-to-br from-blue-500/10 to-blue-500/5 p-4">
                  <div className="text-xs font-bold uppercase tracking-wider text-slate-400">Markup / KM</div>
                  <div className="mt-2 text-3xl font-bold text-white">
                    R${formatNumber(results.markup_km_intermunicipal, 2)}
                  </div>
                  <div className="mt-1 text-xs text-slate-400">Intermunicipais</div>
                  <div className="mt-2 inline-block rounded-full bg-blue-500/20 px-2 py-1 text-xs font-bold text-blue-400">
                    ICMS
                  </div>
                </div>

                <div className="rounded-lg border border-blue-500/50 bg-gradient-to-br from-blue-500/10 to-blue-500/5 p-4">
                  <div className="text-xs font-bold uppercase tracking-wider text-slate-400">Markup / Minuto</div>
                  <div className="mt-2 text-3xl font-bold text-white">
                    R${formatNumber(results.markup_minuto_intermunicipal, 2)}
                  </div>
                  <div className="mt-1 text-xs text-slate-400">Intermunicipais</div>
                  <div className="mt-2 inline-block rounded-full bg-blue-500/20 px-2 py-1 text-xs font-bold text-blue-400">
                    ICMS
                  </div>
                </div>
              </div>

              {/* Tabela de Custos */}
              <div className="rounded-lg border border-slate-700 bg-slate-800/50 overflow-hidden">
                <div className="flex items-center justify-between bg-slate-700/50 px-6 py-4">
                  <div className="text-sm font-bold uppercase tracking-wider text-amber-500">Detalhamento de Custos</div>
                  <div className="text-xs text-slate-400">valores por KM · por hora · mensais · anuais</div>
                </div>
                <div className="overflow-x-auto">
                  <table className="w-full text-sm">
                    <thead>
                      <tr className="border-b border-slate-700 bg-slate-700/30">
                        <th className="px-6 py-3 text-left font-semibold text-slate-400">Item</th>
                        <th className="px-6 py-3 text-right font-semibold text-slate-400">Por KM</th>
                        <th className="px-6 py-3 text-right font-semibold text-slate-400">Por Hora</th>
                        <th className="px-6 py-3 text-right font-semibold text-slate-400">Mensal</th>
                        <th className="px-6 py-3 text-right font-semibold text-slate-400">Anual</th>
                      </tr>
                    </thead>
                    <tbody>
                      <tr className="border-b border-slate-700 bg-amber-500/5">
                        <td colSpan={5} className="px-6 py-2 text-xs font-bold uppercase text-amber-500">
                          CUSTOS FIXOS
                        </td>
                      </tr>
                      {[
                        { label: "Depreciação do Veículo", key: "depreciacao" },
                        { label: "IPVA", key: "ipva" },
                        { label: "Licenciamento + DPVAT", key: "licenciamento" },
                        { label: "Seguro do Veículo", key: "seguro" },
                        { label: "Financiamento / Aluguel", key: "financiamento" },
                        { label: "INSS Pessoa Física", key: "inss" },
                        { label: "Celular / Internet", key: "celular" },
                      ].map((item) => (
                        <tr key={item.key} className="border-b border-slate-700/50 hover:bg-slate-700/20">
                          <td className="px-6 py-3 text-slate-300">{item.label}</td>
                          <td className="px-6 py-3 text-right font-semibold text-white">
                            R${formatNumber(results.por_km[item.key as keyof typeof results.por_km], 4)}
                          </td>
                          <td className="px-6 py-3 text-right font-semibold text-white">
                            R${formatNumber(results.por_hora[item.key as keyof typeof results.por_hora], 2)}
                          </td>
                          <td className="px-6 py-3 text-right font-semibold text-white">
                            R${formatNumber(results.por_mes[item.key as keyof typeof results.por_mes], 2)}
                          </td>
                          <td className="px-6 py-3 text-right font-semibold text-white">
                            R${formatNumber(results.por_ano[item.key as keyof typeof results.por_ano], 2)}
                          </td>
                        </tr>
                      ))}
                      <tr className="border-b border-slate-700 bg-amber-500/5">
                        <td colSpan={5} className="px-6 py-2 text-xs font-bold uppercase text-amber-500">
                          CUSTOS VARIÁVEIS
                        </td>
                      </tr>
                      {[
                        { label: "Alimentação", key: "alimentacao" },
                        { label: "Combustível", key: "combustivel" },
                        { label: "Óleo e Filtro (cada 10k km)", key: "oleo" },
                        { label: "Troca de Pneus", key: "pneus" },
                        { label: "Manutenção Preventiva (peças)", key: "manutencao" },
                        { label: "Lavagem do Veículo", key: "lavagem" },
                      ].map((item) => (
                        <tr key={item.key} className="border-b border-slate-700/50 hover:bg-slate-700/20">
                          <td className="px-6 py-3 text-slate-300">{item.label}</td>
                          <td className="px-6 py-3 text-right font-semibold text-white">
                            R${formatNumber(results.por_km[item.key as keyof typeof results.por_km], 4)}
                          </td>
                          <td className="px-6 py-3 text-right font-semibold text-white">
                            R${formatNumber(results.por_hora[item.key as keyof typeof results.por_hora], 2)}
                          </td>
                          <td className="px-6 py-3 text-right font-semibold text-white">
                            R${formatNumber(results.por_mes[item.key as keyof typeof results.por_mes], 2)}
                          </td>
                          <td className="px-6 py-3 text-right font-semibold text-white">
                            R${formatNumber(results.por_ano[item.key as keyof typeof results.por_ano], 2)}
                          </td>
                        </tr>
                      ))}
                      <tr className="border-b border-slate-700 bg-amber-500/5">
                        <td colSpan={5} className="px-6 py-2 text-xs font-bold uppercase text-amber-500">
                          CUSTOS PERCENTUAIS — BASE ISS (URBANO)
                        </td>
                      </tr>
                      {[
                        { label: "IRPF (imposto de renda estimado)", key: "irpf" },
                        { label: "ISS — Imposto sobre Serviço (5%)", key: "iss_valor" },
                        { label: "Inflação IPCA (4.83%)", key: "ipca_valor" },
                      ].map((item) => (
                        <tr key={item.key} className="border-b border-slate-700/50 hover:bg-slate-700/20">
                          <td className="px-6 py-3 text-slate-300">{item.label}</td>
                          <td className="px-6 py-3 text-right font-semibold text-white">
                            R${formatNumber(results.por_km[item.key as keyof typeof results.por_km], 4)}
                          </td>
                          <td className="px-6 py-3 text-right font-semibold text-white">
                            R${formatNumber(results.por_hora[item.key as keyof typeof results.por_hora], 2)}
                          </td>
                          <td className="px-6 py-3 text-right font-semibold text-white">
                            R${formatNumber(results.por_mes[item.key as keyof typeof results.por_mes], 2)}
                          </td>
                          <td className="px-6 py-3 text-right font-semibold text-white">
                            R${formatNumber(results.por_ano[item.key as keyof typeof results.por_ano], 2)}
                          </td>
                        </tr>
                      ))}
                      <tr className="border-b border-slate-700 bg-amber-500/5">
                        <td colSpan={5} className="px-6 py-2 text-xs font-bold uppercase text-amber-500">
                          CUSTO EXTRA — BASE ICMS (INTERMUNICIPAL, NO LUGAR DE ISS)
                        </td>
                      </tr>
                      <tr className="border-b border-slate-700/50 hover:bg-slate-700/20">
                        <td className="px-6 py-3 text-slate-300">ICMS (12%)</td>
                        <td className="px-6 py-3 text-right font-semibold text-white">
                          R${formatNumber(results.por_km.icms_valor, 4)}
                        </td>
                        <td className="px-6 py-3 text-right font-semibold text-white">
                          R${formatNumber(results.por_hora.icms_valor, 2)}
                        </td>
                        <td className="px-6 py-3 text-right font-semibold text-white">
                          R${formatNumber(results.por_mes.icms_valor, 2)}
                        </td>
                        <td className="px-6 py-3 text-right font-semibold text-white">
                          R${formatNumber(results.por_ano.icms_valor, 2)}
                        </td>
                      </tr>
                      <tr className="border-b border-amber-500 bg-amber-500/10">
                        <td className="px-6 py-3 font-bold text-amber-400">⬛ TOTAL DOS CUSTOS (base ISS)</td>
                        <td className="px-6 py-3 text-right font-bold text-amber-400">
                          R${formatNumber(results.total_custos_iss / (inputs.km_dia * inputs.dias_semana * 4.33), 4)}
                        </td>
                        <td className="px-6 py-3 text-right font-bold text-amber-400">
                          R${formatNumber(results.total_custos_iss / (inputs.horas_dia * inputs.dias_semana * 4.33), 2)}
                        </td>
                        <td className="px-6 py-3 text-right font-bold text-amber-400">
                          R${formatNumber(results.total_custos_iss, 2)}
                        </td>
                        <td className="px-6 py-3 text-right font-bold text-amber-400">
                          R${formatNumber(results.total_custos_iss * 12, 2)}
                        </td>
                      </tr>
                      <tr className="border-b border-blue-500 bg-blue-500/10">
                        <td className="px-6 py-3 font-bold text-blue-400">⬛ TOTAL DOS CUSTOS (base ICMS)</td>
                        <td className="px-6 py-3 text-right font-bold text-blue-400">
                          R${formatNumber(results.total_custos_icms / (inputs.km_dia * inputs.dias_semana * 4.33), 4)}
                        </td>
                        <td className="px-6 py-3 text-right font-bold text-blue-400">
                          R${formatNumber(results.total_custos_icms / (inputs.horas_dia * inputs.dias_semana * 4.33), 2)}
                        </td>
                        <td className="px-6 py-3 text-right font-bold text-blue-400">
                          R${formatNumber(results.total_custos_icms, 2)}
                        </td>
                        <td className="px-6 py-3 text-right font-bold text-blue-400">
                          R${formatNumber(results.total_custos_icms * 12, 2)}
                        </td>
                      </tr>
                      <tr className="bg-green-500/10">
                        <td className="px-6 py-3 font-bold text-green-400">✅ MARKUP FINAL (+ {inputs.margem}% margem, base ISS)</td>
                        <td className="px-6 py-3 text-right font-bold text-green-400">
                          R${formatNumber(results.markup_km_urbano, 4)}
                        </td>
                        <td className="px-6 py-3 text-right font-bold text-green-400">
                          R${formatNumber(results.markup_minuto_urbano * 60, 2)}
                        </td>
                        <td className="px-6 py-3 text-right font-bold text-green-400">
                          R${formatNumber(results.markup_final_iss, 2)}
                        </td>
                        <td className="px-6 py-3 text-right font-bold text-green-400">
                          R${formatNumber(results.markup_final_iss * 12, 2)}
                        </td>
                      </tr>
                    </tbody>
                  </table>
                </div>
              </div>

              {/* Custo por KM */}
              <div className="rounded-lg border border-slate-700 bg-slate-800/50 p-6">
                <div className="text-xs font-bold uppercase tracking-wider text-slate-400">Custo / KM rodado</div>
                <div className="mt-3 text-4xl font-bold text-white">
                  R${formatNumber(results.custo_km, 4)}
                </div>
                <div className="mt-2 text-xs text-slate-400">Gasto real para rodar 1 km (sem lucro)</div>
              </div>
            </div>
          )}
        </div>
      </div>

      {/* Footer */}
      <footer className="border-t border-slate-700 bg-slate-900 px-6 py-8 text-center text-sm text-slate-400">
        Made with <span className="text-amber-500">♥</span> by Manus
      </footer>
    </div>
  );
}
