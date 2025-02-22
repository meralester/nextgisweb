import {useEffect, useCallback, useState} from "react";
import {Button} from "@nextgisweb/gui/antd";
import PropTypes from "prop-types";

import {unByKey} from "ol/Observable";
import {get as getProjection} from "ol/proj";
import {transform, transformExtent} from "ol/proj";

import webmapSettings from "@nextgisweb/pyramid/settings!webmap";
import {getDecPlacesRoundCoordByProj} from "@nextgisweb/webmap/utils/format-units";
import i18n from "@nextgisweb/pyramid/i18n!webmap";

import MouseIcon from "@material-icons/svg/mouse";
import CropFreeIcon from "@material-icons/svg/crop_free";

import "./MapViewerInfo.less";
import {roundValue} from "../utils/format-units.js";

let measureProjCode;
let mapProjCode;
let roundDecPlaces;

const setProjections = (map) => {
    const mapProj = map.getView().getProjection();

    if (!mapProjCode) {
        mapProjCode = map.getView().getProjection().getCode();
    }

    if (!measureProjCode) {
        const proj = getProjection(`EPSG:${webmapSettings.measurement_srid}`);
        measureProjCode = proj ? proj.getCode() : mapProjCode;
        roundDecPlaces = getDecPlacesRoundCoordByProj(proj ? proj : mapProj);
    }
};

const transformCoords = (map, coordinate) => {
    setProjections(map);
    if (measureProjCode === mapProjCode) {
        return coordinate;
    }
    return transform(coordinate, mapProjCode, measureProjCode);
};

const transformMapExtent = (map, extent) => {
    setProjections(map);
    if (measureProjCode === mapProjCode) {
        return extent;
    }
    return transformExtent(extent, mapProjCode, measureProjCode);
};

let pointermoveCallbackKey = undefined;
const clearPointermoveCallback = () => {
    if (pointermoveCallbackKey) {
        unByKey(pointermoveCallbackKey);
        pointermoveCallbackKey = undefined;
    }
};

let viewChangedCallbackKey = undefined;
const clearViewChangedCallback = () => {
    if (viewChangedCallbackKey) {
        unByKey(viewChangedCallbackKey);
        viewChangedCallbackKey = undefined;
    }
};

export function MapViewerInfo({show, map}) {
    if (!map) return <></>;

    const [type, setType] = useState("mouse");
    const [coord, setCoord] = useState(transformCoords(map, map.getView().getCenter()));

    const changeType = () => {
        const newType = type === "mouse" ? "extent" : "mouse";
        setType(newType);
    };

    const bindPointermove = () => {
        pointermoveCallbackKey = map.on("pointermove", pointermoveCallback);
    };
    const pointermoveCallback = useCallback(evt => {
        setCoord(transformCoords(map, evt.coordinate));
    }, []);

    const bindViewChange = () => {
        viewChangedCallbackKey = map.getView().on("change", viewChangeCallback);
    };
    const updateExtent = () => {
        const extent = map.getView().calculateExtent(map.getSize());
        const transformedExtent = transformMapExtent(map, extent);
        setCoord(transformedExtent);
    };
    const viewChangeCallback = useCallback(() => {
        updateExtent();
    }, []);

    useEffect(() => {
        if (!show) {
            clearPointermoveCallback();
            clearViewChangedCallback();
            return;
        }
        if (type === "mouse") {
            clearViewChangedCallback();
            setCoord(transformCoords(map, map.getView().getCenter()));
            bindPointermove();
        } else if (type === "extent") {
            clearPointermoveCallback();
            updateExtent();
            bindViewChange();
        }
    }, [type, show]);

    if (!show) {
        return <></>;
    }

    const icon = type === "mouse" ? <MouseIcon/> : <CropFreeIcon/>;
    const title = type === "mouse" ? i18n.gettext("Show extent") :
        i18n.gettext("Show cursor coordinates");

    let coordinates = "";
    if (coord) {
        if (type === "mouse") {
            coordinates = <>
                <span>{roundValue(coord[0], roundDecPlaces)}, {roundValue(coord[1], roundDecPlaces)}</span>
            </>;
        } else if (type === "extent") {
            coordinates = <>
                <span>{roundValue(coord[0], roundDecPlaces)}, {roundValue(coord[1], roundDecPlaces)}</span>
                <span>:</span>
                <span>{roundValue(coord[2], roundDecPlaces)}, {roundValue(coord[3], roundDecPlaces)}</span>
            </>;
        }
    }

    return (
        <>
            <div className="map-viewer-info">
                <div className={`coordinates type-${type} round-${roundDecPlaces}`}>
                    {coordinates}
                </div>
                <Button
                    className="switch"
                    type="primary"
                    icon={icon}
                    title={title}
                    onClick={() => changeType()}
                />
            </div>
        </>
    );
}

MapViewerInfo.propTypes = {
    show: PropTypes.bool,
    map: PropTypes.object
};
