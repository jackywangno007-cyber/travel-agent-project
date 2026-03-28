/// <reference types="vite/client" />

declare module "*.vue" {
  import type { DefineComponent } from "vue";

  const component: DefineComponent<{}, {}, any>;
  export default component;
}

interface ImportMetaEnv {
  readonly VITE_API_BASE_URL?: string;
  readonly VITE_AMAP_API_KEY?: string;
  readonly VITE_AMAP_SECURITY_JS_CODE?: string;
}

interface ImportMeta {
  readonly env: ImportMetaEnv;
}
