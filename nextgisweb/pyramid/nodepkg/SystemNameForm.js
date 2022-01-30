/** @entrypoint */
import { useState, useEffect } from "react";
import { Button, Input } from "@nextgisweb/gui/antd";

import { route } from "@nextgisweb/pyramid/api";

import ErrorDialog from "ngw-pyramid/ErrorDialog/ErrorDialog";

import i18n from "@nextgisweb/pyramid/i18n!";

export default function () {
    const [fullName, setFullName] = useState();
    const [loading, setLoading] = useState(false);

    useEffect(() => {
        route("pyramid.system_name")
            .get()
            .then((data) => {
                setFullName(data.full_name);
            });
    }, []);

    const saveSystemaName = () => {
        setLoading(true);

        const data = { full_name: fullName };
        route("pyramid.system_name")
            .put({ json: data })
            .then(() => {
                setLoading(false);
                window.location.reload(true);
            })
            .catch((err) => {
                setLoading(false);

                new ErrorDialog(err).show();
            });
    };

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
                    loading={loading}
                    disabled={!fullName}
                    onClick={saveSystemaName}
                >
                    {i18n.gettext("Save")}
                </Button>
            </Input.Group>
        </>
    );
}
