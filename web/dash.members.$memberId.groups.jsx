import { useLoaderData } from "@remix-run/react";
import { getOrganization } from "~/utils/org.server";
import { getUrl, actionHandler } from "~/utils/requests.server";
import { Pagination } from "~/components/pagination/pagination";
import { Toolbar, ToolbarPagination } from "~/components/toolbar/toolbar";
import { usePagination } from "~/hooks/usePagination";
import { GroupCard } from "~/views/groups/groups";

export async function loader({ request, params }) {
    const org = await getOrganization(request);

    const memberId = params.memberId;

    let memberGroupsUrl = getUrl(org.self, "members", memberId, "groups");
    return { groups: { url: memberGroupsUrl }, org };
}

export async function action({ request }) {
    return await actionHandler(request);
}

export default function MemberGroupList() {
    const loaderData = useLoaderData();

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
    } = usePagination(loaderData.groups);

    function renderItem(group) {
        return (
            <GroupCard
                key={`group-${group.id}`}
                group={group}
                active={false}
                selected={false}
            />
        );
    }

    return (
        <Pagination
            fill
            title="Member's Group"
            footer={
                <Toolbar fill margin>
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
            renderItem={renderItem}
            stickyFooter
        />
    );
}
