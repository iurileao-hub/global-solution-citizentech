/** Peças da tela que o contrato não cobre: decodificar o traçado, arredondar como o Python, escolher a
 * receptora da frase de abertura e separar os trechos de chão. */
// @vitest-environment node
import { describe, expect, it } from "vitest";
import { km, nomeLegivel, pct } from "../src/formato";
import { decodificar } from "../src/polyline";
import { redondo } from "../src/nucleo/respostas";

describe("polyline", () => {
  it("decodifica o exemplo da documentação do Google", () => {
    expect(decodificar("_p~iF~ps|U_ulLnnqC_mqNvxq`@")).toEqual([[38.5, -120.2], [40.7, -120.95], [43.252, -126.453]]);
  });
  it("texto vazio é traçado vazio", () => expect(decodificar("")).toEqual([]));
});

describe("arredondamento igual ao do Python", () => {
  it("empate exato vai para o par (12,5 -> 12; 13,5 -> 14)", () => {
    expect([redondo(12.5), redondo(13.5), redondo(0.5), redondo(2.49), redondo(2.51)]).toEqual([12, 14, 0, 2, 3]);
  });
});

describe("formatação", () => {
  it("km com uma casa abaixo de 10", () => expect([km(4.24), km(25.4)]).toEqual(["4,2", "25"]));
  // piso ("pelo menos") arredonda para BAIXO: 24,9 km não pode virar "pelo menos 25"
  it("km de piso nunca passa do valor calculado", () =>
    expect([km(24.9), km(9.96), km(10), km(2.65), km(0.99)]).toEqual(["24", "9,9", "10", "2,6", "0,9"]));
  it("percentual sem ',0' sobrando", () => expect([pct(0.02), pct(0.045), pct(0.35)]).toEqual(["2%", "4,5%", "35%"]));
  it("nome do Censo legível", () => expect(nomeLegivel("EMEF DURVAL MAXIMO DE SOUZA")).toBe("EMEF Durval Maximo de Souza"));
});
