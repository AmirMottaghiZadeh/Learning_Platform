import { Platform } from "react-native";
import { apiClient } from "@/api/client";

export async function exportReferencePdf(id: string) {
  const result=await apiClient.get<ArrayBuffer>(`/uptodate/topics/${encodeURIComponent(id)}/pdf/`,{responseType:"arraybuffer",timeout:120000});
  const bytes=new Uint8Array(result.data);
  if(new TextDecoder().decode(bytes.slice(0,5))!=="%PDF-") throw new Error("PDF export failed");
  const name=`uptodate-${id.replace(/[^A-Za-z0-9_-]/g,"")}.pdf`;
  if(Platform.OS==="web") {
    const url=URL.createObjectURL(new Blob([bytes],{type:"application/pdf"}));
    const anchor=document.createElement("a");anchor.href=url;anchor.download=name;document.body.appendChild(anchor);anchor.click();anchor.remove();
    setTimeout(() => URL.revokeObjectURL(url),60000);return;
  }
  const [{File,Paths},sharing]=await Promise.all([import("expo-file-system"),import("expo-sharing")]);
  const file=new File(Paths.cache,Date.now()+"-"+name);
  await file.create();await file.write(bytes);
  if(!await sharing.isAvailableAsync()) throw new Error("Sharing is unavailable");
  await sharing.shareAsync(file.uri,{mimeType:"application/pdf",UTI:"com.adobe.pdf",dialogTitle:name});
}
