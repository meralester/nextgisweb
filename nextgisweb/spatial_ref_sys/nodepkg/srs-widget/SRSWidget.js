import { Button, Form, Modal } from "@nextgisweb/gui/antd";
import { ContentBox } from "@nextgisweb/gui/component";
import { ModelForm } from "@nextgisweb/gui/model-form";
import { route } from "@nextgisweb/pyramid/api";
import i18n from "@nextgisweb/pyramid/i18n!";
import { PropTypes } from "prop-types";
import { useMemo, useState } from "react";
import getMessages from "../srsMessages";
import { modelObj } from "../srsModel";
import { SRSImportFrom } from "./SRSImportForm";

const DEFAULT_DATA = { projStr: "", format: "proj4" };

export function SRSWidget({ id }) {
    const [isModalVisible, setIsModalVisible] = useState(false);
    const [isProtected, setIsProtected] = useState(false);
    const [isSystem, setIsSystem] = useState(false);
    const [form] = Form.useForm();
    const [modalForm] = Form.useForm();
    const fields = useMemo(() => {
        return [
            {
                name: "display_name",
                label: i18n.gettext("Display name"),
                required: true,
            },
            {
                name: "auth_name_srid",
                label: i18n.gettext("Authority and code"),
                value: (record) => `${record.auth_name}:${record.auth_srid}`,
                disabled: true,
                included: (field, values) =>
                    id !== undefined && values.protected,
            },
            {
                name: "wkt",
                label: i18n.gettext("OGC WKT definition"),
                widget: "textarea",
                rows: 4,
                required: true,
                disabled: isProtected,
            },
        ];
    }, [isProtected]);

    const showModal = () => {
        setIsModalVisible(true);
    };

    const handleOk = async () => {
        try {
            const json = await modalForm.validateFields();
            const resp = await route("spatial_ref_sys.convert").post({
                json,
            });
            if (resp.wkt) {
                const fields = form.getFieldsValue();
                form.setFieldsValue({ ...fields, wkt: resp.wkt });
                setIsModalVisible(false);
            } else if (resp.error) {
                console.log(resp.error);
            }
        } catch (err) {
            if ("message" in err) {
                modalForm.setFields([
                    {
                        name: "projStr",
                        errors: [err.message],
                    },
                ]);
            }
        }
    };

    const handleCancel = () => {
        modalForm.setFieldsValue(DEFAULT_DATA);
        setIsModalVisible(false);
    };

    // to not exec gettext on closed modal
    const Title = () => <>{i18n.gettext("Import definition")}</>;

    const props = {
        id,
        form,
        fields,
        model: modelObj,
        labelCol: { span: 5 },
        messages: getMessages(),
        onChange: (obj) => {
            const v = obj.value;
            if (v) {
                if (v.system !== undefined) {
                    setIsSystem(v.system);
                }
                if (v.protected !== undefined) {
                    setIsProtected(v.protected);
                }
            }
        },
    };

    return (
        <ContentBox>
            <ModelForm allowDelete={!isSystem} {...props}>
                {!isProtected && (
                    <Form.Item wrapperCol={{ offset: 5 }}>
                        <Button size="small" onClick={showModal}>
                            {i18n.gettext("Import definition")}
                        </Button>
                    </Form.Item>
                )}
            </ModelForm>
            <Modal
                title={<Title />}
                open={isModalVisible}
                onOk={handleOk}
                onCancel={handleCancel}
            >
                <SRSImportFrom {...DEFAULT_DATA} form={modalForm} />
            </Modal>
        </ContentBox>
    );
}

SRSWidget.propTypes = {
    id: PropTypes.number,
};
