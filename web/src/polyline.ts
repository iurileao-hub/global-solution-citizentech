/** Decodifica a polyline do Google (precisão 5), o formato dos traçados (src/escola_em_pauta/tracado.py faz o
 * inverso). Cada ponto é a diferença para o anterior, em blocos de 5 bits, com o sinal no bit mais baixo. */
export function decodificar(texto: string, precisao = 5): [number, number][] {
  const f = 10 ** precisao;
  const pontos: [number, number][] = [];
  let i = 0;
  let lat = 0;
  let lon = 0;
  while (i < texto.length) {
    const deltas: number[] = [];
    for (let k = 0; k < 2; k++) {
      let resultado = 0;
      let deslocamento = 0;
      let b: number;
      do {
        b = texto.charCodeAt(i++) - 63;
        resultado |= (b & 0x1f) << deslocamento;
        deslocamento += 5;
      } while (b >= 0x20);
      deltas.push(resultado & 1 ? ~(resultado >> 1) : resultado >> 1);
    }
    lat += deltas[0];
    lon += deltas[1];
    pontos.push([lat / f, lon / f]);
  }
  return pontos;
}
