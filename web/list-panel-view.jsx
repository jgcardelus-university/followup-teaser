import React, { useEffect, useImperativeHandle } from "react";
import { Spinner } from "../spinner/spinner";
import { Pagination } from "../pagination/pagination";
import { Toolbar, ToolbarPagination } from "../toolbar/toolbar";

import { usePagination } from "~/hooks/usePagination";
import { OutletPanelView } from "./outlet-panel-view";
import { EmptyDetail } from "~/views/utils/utils";

export const ListPanelView = React.forwardRef((props, ref) => {
    const {
        items,
        currentPage,
        lastPage,
        isLoading,
        isFirst,
        isLast,
        filter,
        first,
        next,
        jump,
        previous,
        last,
        setItem,
    } = usePagination(props.data);

    useEffect(() => {
        filter(props.filterValues);
    }, [props.filterValues]);

    useImperativeHandle(ref, () => {
        return {
            setItem(item) {
                setItem(item);
            },
        };
    });

    return (
        <OutletPanelView
            placeholder={<EmptyDetail message={props.emptyMessage} />}
            outlet={props.active && !props.isSelecting}
            outletContext={props.outletContext}
            autoSaveId={props.autoSaveId}
            popOutlet={props.popOutlet}
        >
            {!props.data ? (
                <Spinner />
            ) : (
                <Pagination
                    fill
                    title={props.title}
                    sticky={props.filters}
                    footer={
                        <Toolbar fill margin>
                            {props.toolbarElements}
                            <ToolbarPagination
                                currentPage={currentPage}
                                lastPage={lastPage}
                                isLoading={isLoading}
                                isFirst={isFirst}
                                isLast={isLast}
                                first={first}
                                previous={previous}
                                next={next}
                                last={last}
                            />
                        </Toolbar>
                    }
                    items={items}
                    isLoading={isLoading}
                    renderItem={props.renderItem}
                    stickyFooter
                />
            )}
        </OutletPanelView>
    );
});

ListPanelView.displayName = "ListPanelView";
