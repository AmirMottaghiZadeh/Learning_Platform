export const PEDIATRIC_ENGINE_SHA256 = "b728c6580b1779e8318edf52f9fb1c7b2f41ff1e5bcb00d93ebe19ff449132bf";

export function isCompatibleDataset(data: { schema_version?: unknown; engine_sha256?: unknown }) {
  return data.schema_version === 1 && data.engine_sha256 === PEDIATRIC_ENGINE_SHA256;
}
