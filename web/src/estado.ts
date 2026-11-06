/** Cada navegação ganha um número. Uma tela que terminou de carregar depois que a pessoa já foi para outra
 * (rede lenta) confere o número antes de desenhar, e desiste se ele ficou velho. */
let geracao = 0;

export function novaGeracao(): number {
  return ++geracao;
}

export function vivo(g: number): boolean {
  return g === geracao;
}
