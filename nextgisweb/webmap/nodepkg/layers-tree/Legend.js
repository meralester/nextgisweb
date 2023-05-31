import { useEffect, useState } from "react";
import PropTypes from "prop-types";

import { Row, Col } from "@nextgisweb/gui/antd";
import { route } from "@nextgisweb/pyramid/api";
import i18n from "@nextgisweb/pyramid/i18n!webmap";

import ViewListIcon from "@material-icons/svg/view_list/outline";
import ExpandLessIcon from "@material-icons/svg/expand_less/outline";

import "./Legend.less";

const showLegendMessage = i18n.gettext("Show legend");
const hideLegendMessage = i18n.gettext("Hide legend");

export function LegendAction({
                                 nodeData,
                                 onClick
                             }) {
    if (!nodeData || !nodeData.legendInfo) {
        return <></>;
    }

    const { open } = nodeData.legendInfo;
    const icon = open ? <ExpandLessIcon/> : <ViewListIcon/>;

    const click = () => {
        const { id } = nodeData;
        const { open } = nodeData.legendInfo;
        nodeData.legendInfo.open = !open;

        onClick(id);
    };

    return (
        <span
            className="legend"
            onClick={click}
            title={open ? hideLegendMessage : showLegendMessage}
        >
            {icon}
        </span>
    );
}


export function Legend({
                           nodeData
                       }) {


    const [legendData, setLegendData] = useState(undefined);

    const { open } = nodeData.legendInfo ?? {};

    useEffect(async () => {
        if (!open || legendData) {
            return;
        }

        const { styleId } = nodeData;
        const getSymbols = route("render.legend_symbols", styleId).get();
        const minTime = new Promise(r => setTimeout(r, 1000));
        const symbols = await Promise.all([getSymbols, minTime]);
        setLegendData(symbols[0]);
    }, [open]);

    if (!nodeData || !nodeData.legendInfo) {
        return <></>;
    }

    if (!open) {
        return <></>;
    }

    let legend;
    if (legendData) {
        legend = <>
            {
                legendData.map((s, idx) => (
                    <div key={idx} className="legend-symbol">
                        <img width={24} height={24} src={"data:image/png;base64," + s.icon.data}/>
                        <div>{s.display_name}</div>
                    </div>
                ))
            }
        </>;
    } else {
        legend = (
            <div className="linear-activity">
                <div className="indeterminate"></div>
            </div>
        );
    }

    return <Row wrap={false}>
        <Col flex="auto">
            {legend}
        </Col>
    </Row>;
}

LegendAction.propTypes = {
    nodeData: PropTypes.object,
    onClick: PropTypes.func
};

Legend.propTypes = {
    nodeData: PropTypes.object
};
