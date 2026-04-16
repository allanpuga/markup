export interface CidadeData {
  iss: number;
}

export interface EstadoData {
  nome: string;
  icms: number;
  ipva: number;
  gas: number;
  cidades: Record<string, number>;
}

export const estadosData: Record<string, EstadoData> = {
  AC: {
    nome: "Acre",
    icms: 12,
    ipva: 3,
    gas: 5.8,
    cidades: {
      "Rio Branco": 5,
      Cruzeiro: 5,
      Tarauaca: 5,
    },
  },
  AL: {
    nome: "Alagoas",
    icms: 12,
    ipva: 3.5,
    gas: 5.95,
    cidades: {
      Maceio: 5,
      Arapiraca: 5,
      Penedo: 5,
    },
  },
  AP: {
    nome: "Amapa",
    icms: 12,
    ipva: 3,
    gas: 6.1,
    cidades: {
      Macapa: 5,
      Santana: 5,
    },
  },
  AM: {
    nome: "Amazonas",
    icms: 12,
    ipva: 3,
    gas: 6.2,
    cidades: {
      Manaus: 5,
      Parintins: 5,
      Itacoatiara: 5,
    },
  },
  BA: {
    nome: "Bahia",
    icms: 12,
    ipva: 3.5,
    gas: 5.92,
    cidades: {
      Salvador: 5,
      Feira: 5,
      Vitoria: 5,
      Camaçari: 5,
      Ilheus: 5,
    },
  },
  CE: {
    nome: "Ceara",
    icms: 12,
    ipva: 3.5,
    gas: 5.88,
    cidades: {
      Fortaleza: 5,
      Caucaia: 5,
      Juazeiro: 5,
      Sobral: 5,
    },
  },
  DF: {
    nome: "Distrito Federal",
    icms: 12,
    ipva: 3.5,
    gas: 5.85,
    cidades: {
      Brasilia: 5,
    },
  },
  ES: {
    nome: "Espirito Santo",
    icms: 12,
    ipva: 3.5,
    gas: 5.9,
    cidades: {
      Vitoria: 5,
      "Vila Velha": 5,
      Cariacica: 5,
      Serra: 5,
    },
  },
  GO: {
    nome: "Goias",
    icms: 12,
    ipva: 3.5,
    gas: 5.87,
    cidades: {
      Goiania: 5,
      Anapolis: 5,
      Aparecida: 5,
    },
  },
  MA: {
    nome: "Maranhao",
    icms: 12,
    ipva: 3,
    gas: 5.93,
    cidades: {
      "Sao Luis": 5,
      Imperatriz: 5,
      Caxias: 5,
    },
  },
  MT: {
    nome: "Mato Grosso",
    icms: 12,
    ipva: 3.5,
    gas: 5.89,
    cidades: {
      Cuiaba: 5,
      Varzea: 5,
      Rondonopolis: 5,
    },
  },
  MS: {
    nome: "Mato Grosso do Sul",
    icms: 12,
    ipva: 3.5,
    gas: 5.86,
    cidades: {
      "Campo Grande": 5,
      Dourados: 5,
      "Tres Lagoas": 5,
    },
  },
  MG: {
    nome: "Minas Gerais",
    icms: 12,
    ipva: 3.5,
    gas: 5.91,
    cidades: {
      "Belo Horizonte": 5,
      Uberlandia: 5,
      Contagem: 5,
      Juiz: 5,
      Montes: 5,
    },
  },
  PA: {
    nome: "Para",
    icms: 12,
    ipva: 3,
    gas: 6.05,
    cidades: {
      Belem: 5,
      Ananindeua: 5,
      Maraba: 5,
    },
  },
  PB: {
    nome: "Paraiba",
    icms: 12,
    ipva: 3.5,
    gas: 5.94,
    cidades: {
      "Joao Pessoa": 5,
      Campina: 5,
      Patos: 5,
    },
  },
  PR: {
    nome: "Parana",
    icms: 12,
    ipva: 3.5,
    gas: 5.88,
    cidades: {
      Curitiba: 5,
      Londrina: 5,
      Maringa: 5,
      Ponta: 5,
      Cascavel: 5,
    },
  },
  PE: {
    nome: "Pernambuco",
    icms: 12,
    ipva: 3.5,
    gas: 5.96,
    cidades: {
      Recife: 5,
      Jaboatao: 5,
      Olinda: 5,
      Caruaru: 5,
    },
  },
  PI: {
    nome: "Piaui",
    icms: 12,
    ipva: 3,
    gas: 5.92,
    cidades: {
      Teresina: 5,
      Parnaiba: 5,
      Picos: 5,
    },
  },
  RJ: {
    nome: "Rio de Janeiro",
    icms: 12,
    ipva: 3.5,
    gas: 5.89,
    cidades: {
      Rio: 5,
      Niteroi: 5,
      Duque: 5,
      Nova: 5,
      Sao: 5,
    },
  },
  RN: {
    nome: "Rio Grande do Norte",
    icms: 12,
    ipva: 3.5,
    gas: 5.97,
    cidades: {
      Natal: 5,
      Mossoro: 5,
      Parnamirim: 5,
    },
  },
  RS: {
    nome: "Rio Grande do Sul",
    icms: 12,
    ipva: 3.5,
    gas: 5.87,
    cidades: {
      "Porto Alegre": 5,
      Caxias: 5,
      Pelotas: 5,
      Santa: 5,
      Novo: 5,
    },
  },
  RO: {
    nome: "Rondonia",
    icms: 12,
    ipva: 3,
    gas: 6.0,
    cidades: {
      "Porto Velho": 5,
      Ariquemes: 5,
      Ji: 5,
    },
  },
  RR: {
    nome: "Roraima",
    icms: 12,
    ipva: 3,
    gas: 6.15,
    cidades: {
      Boa: 5,
      Manaus: 5,
    },
  },
  SC: {
    nome: "Santa Catarina",
    icms: 12,
    ipva: 3.5,
    gas: 5.86,
    cidades: {
      Florianopolis: 5,
      Joinville: 5,
      Blumenau: 5,
      Chapeco: 5,
    },
  },
  SP: {
    nome: "Sao Paulo",
    icms: 12,
    ipva: 4,
    gas: 5.85,
    cidades: {
      "Sao Paulo": 5,
      Campinas: 4,
      Santos: 5,
      Sorocaba: 5,
      Ribeirao: 5,
      Piracicaba: 5,
      Araraquara: 5,
      Bauru: 5,
      Jundiai: 5,
      Mogi: 5,
    },
  },
  SE: {
    nome: "Sergipe",
    icms: 12,
    ipva: 3.5,
    gas: 5.94,
    cidades: {
      Aracaju: 5,
      Lagarto: 5,
      Nossa: 5,
    },
  },
  TO: {
    nome: "Tocantins",
    icms: 12,
    ipva: 3,
    gas: 5.88,
    cidades: {
      Palmas: 5,
      Araguaina: 5,
      Gurupi: 5,
    },
  },
};
