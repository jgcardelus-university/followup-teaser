const scheme = {
    navigation: {
        pages: {
            current: 0,
            last: 0,
        },
        self: null,
        next: null,
        last: null,
        count: 0,
    },
    results: [],
};

export function usePagination(rawInitialData) {
    const fetcher = useFetcher();

    const [items, setItems] = useState([]);
    const [lastRequest, setLastRequest] = useState(scheme);
    const [currentPage, setCurrentPage] = useState(1);
    const [lastPage, setLastPage] = useState(1);

    const [isLast, setIsLast] = useState(false);
    const [isFirst, setIsFirst] = useState(false);

    const [url, setUrl] = useState();

    useEffect(() => {
        if (!url || rawInitialData.url != url) {
            setUrl(rawInitialData.url);
            submit(rawInitialData.url);
        }
    }, [rawInitialData, url]);

    useEffect(() => {
        if (!fetcher.data || fetcher.state === "loading") {
            return;
        }

        // If we have new data - set it
        if (fetcher.data?.ok) {
            // set pagination data
            set(fetcher.data.json);
        }
    }, [fetcher.data, fetcher.state]);

    function set(data) {
        setLastRequest(data);
        setItems(data.results);
        setCurrentPage(data.navigation.pages.current);
        setLastPage(data.navigation.pages.last);
        setIsLast(data.navigation.next === null);
        setIsFirst(data.navigation.previous === null);
    }

    function setItem(item) {
        setItems((prev) => {
            let copy = [...prev];
            const index = copy.findIndex((check, index) => {
                return item.id === check.id;
            });
            copy[index] = item;
            return [...copy];
        });
    }

    function destroyItem(item) {
        setItems((prev) => {
            let copy = [...prev];
            const index = copy.findIndex((check, index) => {
                if (item.id === check.id) {
                    return true;
                }
                return false;
            });
            copy.splice(index, 1);
            return [...copy];
        });
    }

    function submit(url) {
        if (fetcher.state === "idle" && url !== null && url != undefined) {
            fetcher.submit(
                { intent: PAGINATION_INTENT, url: url },
                { method: "POST" }
            );
        }
    }

    function filter(values) {
        let url = lastRequest.navigation.current;
        Object.entries(values).forEach(([key, value]) => {
            url = updateQueryParam(key, value, url);
        });

        submit(url);
    }

    function first() {
        const url = updateQueryParam(
            "page",
            undefined,
            lastRequest.navigation.current
        );
        submit(url);
    }

    function last() {
        const url = updateQueryParam(
            "page",
            "last",
            lastRequest.navigation.current
        );
        submit(url);
    }

    function next() {
        let nextUrl = lastRequest.navigation.next;
        submit(nextUrl);
    }

    function previous() {
        let previousUrl = lastRequest.navigation.previous;
        submit(previousUrl);
    }

    function jump(page) {
        if (page != undefined && typeof page !== "number") {
            throw Error("Invalid page");
        }

        if (page > 0 && page <= lastPage) {
            const url = updateQueryParam(
                "page",
                page,
                lastRequest.navigation.current
            );

            submit(url);
        }
    }

    const isLoading =
        fetcher.state === "loading" || fetcher.state === "submitting";

    return {
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
        destroyItem,
    };
}
