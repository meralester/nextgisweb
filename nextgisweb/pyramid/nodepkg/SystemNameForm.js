/** @entrypoint */
import { useState, useEffect } from "react";
import { observer } from "mobx-react-lite";
import { Button, Input } from "@nextgisweb/gui/antd";

import pyramidStore from "@nextgisweb/pyramid/store";

import ErrorDialog from "ngw-pyramid/ErrorDialog/ErrorDialog";

import i18n from "@nextgisweb/pyramid/i18n!";

const SystemNameForm = observer(() => {
  const [systemName] = useState(() => pyramidStore.systemNameStore);

  const [fullName, setFullName] = useState(systemName.fullName);

  const saveSystemaName = () => {
    systemName.setFullName(fullName).catch((err) => {
      new ErrorDialog(err).show();
    });
  };

  useEffect(() => {
    setFullName(systemName.fullName);
  }, [systemName.fullName]);

  return (
    <>
      <Input.Group compact>
        <Input
          value={fullName}
          style={{ width: "calc(100% - 200px)" }}
          onChange={(e) => setFullName(e.target.value)}
        />
        <Button
          type="primary"
          loading={systemName.isLoading}
          disabled={!fullName}
          onClick={saveSystemaName}
        >
          {i18n.gettext("Save")}
        </Button>
      </Input.Group>
    </>
  );
});

export default SystemNameForm;
