import PropTypes from "prop-types";

import { useCallback, useEffect, useState, useMemo } from "react";

import ManageSearchIcon from "@material-icons/svg/manage_search";
import DeleteIcon from "@material-icons/svg/delete";

import { Button, Form, Input, Space, Table } from "@nextgisweb/gui/antd";
import {
    showResourcePicker,
    ResourcePickerStore,
} from "@nextgisweb/resource/resource-picker";
import { route, routeURL } from "@nextgisweb/pyramid/api";
import { useAbortController } from "@nextgisweb/pyramid/hook/useAbortController";

const SelectInput = ({
    value: initResourceIds = [],
    onChange,
    ...pickerOptions
}) => {
    const { makeSignal, abort } = useAbortController();
    const [selectedRowKeys, setSelectedRowKeys] = useState([]);
    const [ids, setIds] = useState(
        // Remove duplicates
        [...new Set(initResourceIds)]
    );
    const [resources, setResources] = useState([]);
    const [loading, setLoading] = useState(false);
    const [total] = useState(20);

    const [store] = useState(() => new ResourcePickerStore(pickerOptions));

    const bottom = useMemo(() => {
        return resources.length > total ? "bottomCenter " : "none";
    }, [resources, total]);

    const onSelect = (addIds) => {
        const newIds = [...ids];
        for (const addId of addIds) {
            if (!newIds.includes(addId)) {
                newIds.push(addId);
            }
        }
        onChange(newIds);
        setIds(newIds);
    };

    const loadResources = useCallback(async () => {
        abort();
        setLoading(true);

        const promises = [];
        const getOpt = {
            cache: true,
            signal: makeSignal(),
        };
        for (const id of ids) {
            const promise = Promise.all([
                route("resource.item", id).get(getOpt),
            ]);
            promises.push(promise);
        }
        try {
            const resp = await Promise.all(promises);
            const resources_ = resp.map((r) => {
                const res = r[0].resource;
                delete res.children;
                return res;
            });
            setResources(
                resources_.filter((r) => store.checkEnabled.call(store, r))
            );
        } finally {
            setLoading(false);
        }
    }, [ids, abort, makeSignal, store]);

    const columns = [
        {
            title: "Name",
            dataIndex: "display_name",
            render: (text, row) => {
                return (
                    <a
                        href={routeURL("resource.show", row.id)}
                        onClick={(evt) => evt.stopPropagation()}
                        target="_blank"
                        rel="noreferrer"
                    >
                        {text}
                    </a>
                );
            },
        },
    ];

    const onSelectChange = (newSelectedRowKeys) => {
        setSelectedRowKeys(newSelectedRowKeys);
    };

    const onClick = () => {
        (store.disabledIds = ids),
        (store.selected = ids),
        showResourcePicker({
            ...pickerOptions,
            store,
            onSelect,
        });
    };

    const removeSelected = () => {
        setIds((old) => {
            if (selectedRowKeys.length) {
                return old.filter((oldId) => !selectedRowKeys.includes(oldId));
            }
            return old;
        });
    };

    const rowSelection = {
        selectedRowKeys,
        onChange: onSelectChange,
    };

    useEffect(() => {
        loadResources();
        setSelectedRowKeys((old) => {
            return old.filter((oldId) => !ids.includes(oldId));
        });
    }, [ids, loadResources]);

    return (
        <Input.Group compact>
            <div style={{ width: "100%" }}>
                <div style={{ marginBottom: 16 }}>
                    <Space>
                        <Button
                            disabled={!selectedRowKeys.length}
                            onClick={removeSelected}
                            icon={<DeleteIcon />}
                        />
                        <Button onClick={onClick} icon={<ManageSearchIcon />} />
                    </Space>
                </div>
                <Table
                    rowKey="id"
                    rowSelection={rowSelection}
                    dataSource={resources}
                    columns={columns}
                    showHeader={false}
                    loading={loading}
                    pagination={{ position: ["none", bottom], total }}
                />
            </div>
        </Input.Group>
    );
};

SelectInput.propTypes = {
    onChange: PropTypes.func,
    value: PropTypes.any,
};

export function ResourceSelectMultiple({ pickerOptions, ...props }) {
    return (
        <Form.Item {...props}>
            <SelectInput {...pickerOptions}></SelectInput>
        </Form.Item>
    );
}

ResourceSelectMultiple.propTypes = {
    pickerOptions: PropTypes.object,
};
