import { makeAutoObservable, runInAction } from "mobx";
import { route } from "@nextgisweb/pyramid/api";

class SystemNameStore {
  isLoading = false;
  errors = undefined;

  fullName = "";

  constructor(rootStore) {
    makeAutoObservable(this, { rootStore: false });
    this.rootStore = rootStore;
    route("pyramid.system_name")
      .get()
      .then((data) => {
        runInAction(() => {
          this.fullName = data.full_name;
        });
      });
  }

  setFullName(fullName) {
    this.isLoading = true;
    this.errors = undefined;
    const data = { full_name: fullName };
    return route("pyramid.system_name")
      .put({ json: data })
      .then(() => {
        runInAction(() => {
          this.fullName = fullName;
        });
      })
      .catch((err) => {
        runInAction(() => {
          this.errors = [err];
          throw err;
        });
      })
      .finally(() => {
        runInAction(() => {
          this.isLoading = false;
        });
      });
  }
}

export default SystemNameStore;
