import { useEffect, useRef, useCallback } from "react";

import { AbortControllerHelper } from "@nextgisweb/pyramid/util/abort";

export function useAbortController() {
    const abortHelper = useRef();

    const makeSignal = useCallback(() => {
        return abortHelper.current.makeSignal();
    }, []);

    const abort = useCallback(() => {
        abortHelper.current.abort();
    }, []);

    useEffect(() => {
        const abortHelper_ = new AbortControllerHelper();
        abortHelper.current = abortHelper_;
        return () => abortHelper_.abort();
    }, []);

    return { makeSignal, abort };
}
