define([
    "dojo/_base/declare",
    "dojo/_base/array",
    "ngw-pyramid/make-singleton"
], function (
    declare,
    array,
    MakeSingleton
) {
    return MakeSingleton(declare("ngw-webmap.MapStatesObserver", [], {
        _states: {},
        _defaultState: null,
        _currentState: null,

        constructor: function (options) {
            if (!options) {
                return true;
            }

            if (options.states) {
                array.forEach(options.states, function (stateItem) {
                    this.addState(stateItem.state, stateItem.control);
                }, this);
            }

            if (options.defaultState) {
                this.setDefaultState(options.defaultState);
            }
        },

        addState: function (state, control, activate) {

            if (this._states.hasOwnProperty(state)) {
                throw new Error("State \"" + state + "\" already registered.");
            }

            this._states[state] = {
                control: control ? control : null
            };

            if (activate) {
                this.activateState(state);
            }
        },

        removeState: function (state) {
            delete this._states[state];
        },

        activateState: function (state) {
            if (!this._states.hasOwnProperty(state)) {
                return false;
            }

            const affectGlobalState = this.shouldAffectState(state);
            if (this._currentState &&
                this._currentState === state &&
                affectGlobalState
            ) return true;

            if (this._currentState && affectGlobalState) {
                var currentControl = this._states[this._currentState].control;
                if (currentControl) currentControl.deactivate();
            }

            var stateControl = this._states[state].control;
            if (stateControl) stateControl.activate();

            if (affectGlobalState) this._currentState = state;
            return true;
        },

        deactivateState: function (state) {
            const affectGlobalState = this.shouldAffectState(state);
            if (!this._states.hasOwnProperty(state) ||
                state !== this._currentState &&
                affectGlobalState) {
                return false;
            }

            var stateControl = this._states[state].control;
            if (stateControl) stateControl.deactivate();

            if (this._defaultState &&
                this._defaultState !== state &&
                affectGlobalState) {
                this._currentState = null;
                this.activateState(this._defaultState);
            }
            return true;
        },

        shouldAffectState: function (stateName) {
            return stateName.substring(0, 1) !== "~";
        },

        setDefaultState: function (state, activate) {
            this._defaultState = state;
            if (activate) {
                this.activateState(state);
            }
        },

        activateDefaultState: function () {
            this.activateState(this._defaultState);
        },

        getActiveState: function () {
            if (!this._currentState) return false;
            return this._currentState;
        }
    }));
});
