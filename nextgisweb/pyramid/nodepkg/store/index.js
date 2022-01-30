import SystemNameStore from "./SystemNameStore";

class PyramidStore {
  constructor() {
    this.systemNameStore = new SystemNameStore(this);
  }
}

export default new PyramidStore();
